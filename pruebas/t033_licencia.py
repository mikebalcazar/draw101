"""t033 · Licencias: la firma y el motor.

draw101 se vende **por suscripción mensual, se corta si no paga**. Esta prueba
cubre la parte que vive en draw101; las claves y los cobros son de
suite101-api (Jr., API 0.13.0).

Lo que se comprueba, que es lo que puede costar dinero o enemigos:

  · La **firma** Ed25519 escrita en Python puro (`core/firma.py`) acepta las
    firmas buenas y rechaza las alteradas, las de otra llave y la basura. Se
    prueba contra firmas hechas con `cryptography`, una biblioteca de verdad,
    que se usa **sólo aquí**: dentro del programa no va ninguna.
  · Un permiso **inventado o retocado** no pasa.
  · Un permiso **de otra computadora** no pasa.
  · Sin activar, draw101 abre en **modo lectura** (Mike, 18-sep: no hay
    periodo de prueba; una clave no abre nada hasta que él la marca pagada o
    de cortesía).
  · Una suscripción **al corriente** deja escribir; una **vencida** no.
  · Un permiso **de otro programa** de la suite no abre éste, aunque la llave
    del servidor sea la misma para los tres.
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import pathlib
import tempfile

from pruebas import comun

DESCRIPCION = "licencias: firma, activación, vencimiento y permisos ajenos"


def _hay_cryptography() -> bool:
    try:
        import cryptography  # noqa: F401
        return True
    except Exception:
        return False


def correr(r: comun.Reporte) -> None:
    if not _hay_cryptography():
        r.cierto(True, "(sin `cryptography` para fabricar firmas: la prueba se salta)")
        return
    _firma(r)
    _motor(r)


# --- Un Taller 101 de mentira ----------------------------------------------

def _taller():
    """Una llave nueva y una función que firma permisos, como haría el API."""
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)

    def firmar(datos: dict) -> str:
        carga = json.dumps(datos).encode("utf-8")
        b = base64.urlsafe_b64encode(carga).decode().rstrip("=")
        f = base64.urlsafe_b64encode(sk.sign(carga)).decode().rstrip("=")
        return f"v1.{b}.{f}"            # el formato del servidor de Jr.

    return pk.hex(), firmar


def _firma(r: comun.Reporte) -> None:
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from core import firma

    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
    otra = Ed25519PrivateKey.generate().public_key().public_bytes(
        ser.Encoding.Raw, ser.PublicFormat.Raw)

    for mensaje in (b"", b"hola", b'{"cliente":"Taller 101"}' * 20):
        rubrica = sk.sign(mensaje)
        r.cierto(firma.verificar(pk, mensaje, rubrica),
                 f"la firma buena de un mensaje de {len(mensaje)} bytes se acepta")
        mala = bytearray(rubrica)
        mala[7] ^= 1
        r.cierto(not firma.verificar(pk, mensaje, bytes(mala)),
                 "una firma alterada se rechaza")
        r.cierto(not firma.verificar(otra, mensaje, rubrica),
                 "y con otra llave también se rechaza")
    r.cierto(not firma.verificar(b"corta", b"x", b"basura"), "la basura se rechaza sin tronar")
    r.cierto(not firma.verificar(b"\x00" * 32, b"x", b"\x00" * 64),
             "una llave de ceros con firma de ceros tampoco pasa")


# --- El motor ---------------------------------------------------------------

def _motor(r: comun.Reporte) -> None:
    from core import config, licencia

    carpeta = pathlib.Path(tempfile.mkdtemp())
    publica, firmar = _taller()
    viejo_llave, viejo_carpeta = licencia.LLAVE_PUBLICA, config.carpeta_usuario
    licencia.LLAVE_PUBLICA = publica
    config.carpeta_usuario = lambda: carpeta                      # type: ignore
    try:
        hoy = dt.date.today()
        maquina = licencia.huella_maquina()

        def permiso(dias: int, **extra) -> str:
            base = {"v": 1, "kid": "prueba", "programa": "draw101",
                    "licencia": "01K5", "cliente": "Carpintería Ruiz",
                    "plan": "mensual", "lugares": 1, "maquina": maquina,
                    "emitido": hoy.isoformat() + "T00:00:00.000Z",
                    "hasta": (hoy + dt.timedelta(days=dias)).isoformat() + "T02:40:11.000Z"}
            base.update(extra)
            return firmar(base)

        def poner(token: str) -> None:
            (carpeta / "licencia.json").write_text(json.dumps({"token": token}))

        # 1. Recién instalado, sin clave: modo lectura. (Mike, 18-sep: no hay
        # periodo de prueba; una clave no abre nada hasta que él la marca.)
        e = licencia.estado()
        r.igual(e["estado"], "sin_activar", "sin activar, draw101 no escribe")
        r.cierto(not e["puede_escribir"], "y queda en modo lectura")

        # 2. Activado y al corriente.
        poner(permiso(30))
        e = licencia.estado()
        r.igual(e["estado"], "activa", "con la suscripción al corriente queda activa")
        r.igual(e["cliente"], "Carpintería Ruiz", "y sabe de quién es")
        r.igual(e["licencia"], "01K5", "y de qué licencia")
        r.cierto(e["puede_escribir"], "y se puede trabajar")

        # 3. Ya mero vence: avisa, pero no estorba.
        poner(permiso(3))
        e = licencia.estado()
        r.igual(e["estado"], "por_vencer", "a tres días avisa que va a vencer")
        r.cierto(e["puede_escribir"], "pero deja trabajar")

        # 4. Venció: modo lectura. El margen ya venía dentro de la fecha (el
        # servidor pone lo que llegue antes entre el día pagado y 30 días desde
        # el latido), así que aquí no se suma nada encima.
        poner(permiso(-1))
        e = licencia.estado()
        r.igual(e["estado"], "vencida", "pasada la fecha, se corta")
        r.cierto(not e["puede_escribir"], "y ya no se puede guardar ni exportar")

        # 5. Un permiso retocado a mano no vale.
        version, cuerpo, rubrica = permiso(-1).split(".")
        datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
        datos["hasta"] = "2099-12-31T00:00:00.000Z"
        falso = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode().rstrip("=")
        poner(f"v1.{falso}.{rubrica}")
        r.igual(licencia.estado()["estado"], "sin_activar",
                "cambiarle la fecha al permiso no sirve: la firma ya no cuadra")

        # 6. El permiso de otra computadora tampoco.
        poner(permiso(30, maquina="otra-maquina-cualquiera"))
        r.igual(licencia.estado()["estado"], "sin_activar",
                "un permiso emitido para otra máquina no abre ésta")

        # 7. Ni el de otro programa de la suite: la llave es la misma para los
        # tres, y lo que separa es el campo «programa».
        poner(permiso(30, programa="nest101"))
        r.igual(licencia.estado()["estado"], "sin_activar",
                "un permiso de nest101 no abre draw101")

        # 8. Un token con otra versión de formato se rechaza en vez de adivinar.
        poner(permiso(30).replace("v1.", "v2.", 1))
        r.igual(licencia.estado()["estado"], "sin_activar",
                "un token «v2» no se interpreta a la fuerza")

        # 9. La huella es estable dentro de la misma máquina.
        r.igual(licencia.huella_maquina(), maquina, "la huella de la máquina no cambia sola")
        r.igual(len(maquina), 64, "y es un resumen, no los datos de la persona")
    finally:
        licencia.LLAVE_PUBLICA = viejo_llave
        config.carpeta_usuario = viejo_carpeta                    # type: ignore
