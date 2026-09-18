"""Licencias de draw101  ·  0.20.18

draw101 se vende a terceros **por suscripción mensual, y se corta si no paga**.

Cómo funciona, en el idioma del taller:

  · Sin clave no se trabaja: draw101 abre en **modo lectura** —ver, medir e
    imprimir— hasta que se active. (El 16-sep se habían decidido 15 días de
    prueba; el 18-sep Mike decidió que no hay prueba, y así quedó el servidor:
    una clave no abre nada hasta que él la marca pagada o de cortesía.)
  · Con una clave (`T101-XXXX-XXXX-XXXX`) se **activa**: el servidor de Taller
    101 apunta esa máquina y contesta un permiso **firmado** que dice hasta
    cuándo vale. draw101 lo guarda y comprueba la firma cada vez que abre.
  · Una vez al día pide un **latido**: si la suscripción sigue pagada, el
    servidor corre la fecha; si no, deja de correrla y el permiso vence solo.
  · La fecha del permiso ya trae el margen: el servidor pone **lo que llegue
    antes entre el fin del día pagado y 30 días desde el latido**. Por eso aquí
    no se suma ningún margen encima —serían 30 + 14 y un moroso duraría mes y
    medio—: mientras el permiso no venza se trabaja, y sin internet eso da
    hasta 30 días.
  · Vencido, la app entra en **modo lectura**: se puede ver, medir e imprimir,
    pero no guardar ni exportar. Cortar en seco con un plano abierto sin
    guardar sería peor que no cobrar.

Lo que este archivo NO hace, a propósito:

  · **No firma.** Firmar es del servidor, con la llave privada. Aquí sólo vive
    la pública (ver `LLAVE_PUBLICA`), y con la pública no se fabrica un
    permiso.
  · **No cobra.** Los cobros, las claves y las revocaciones viven en
    suite101-api. Ver el contrato en Drive, `draw101-licencias-etapa1`.
  · **Todavía no estorba.** En 0.20.18 nadie llama a `puede_escribir()`: la
    maquinaria entra primero, la pantalla de activación y el modo lectura
    después, cuando Mike lo diga. Así una versión nueva no deja a nadie sin
    guardar por un error de este archivo.

Y lo que hay que decir en voz alta: esto es **control comercial, no
protección**. El código de draw101 va en claro dentro del instalador, así que
quien sepa puede saltarse este archivo. Lo que de verdad protege es que lo
valioso viva en el servidor (leer DWG, despiece, catálogo): la etapa 2.
"""

from __future__ import annotations

import base64
import datetime as dt
import getpass
import hashlib
import json
import pathlib
import platform
import time
import urllib.error
import urllib.request

from . import config
from . import firma as mod_firma

#: La llave pública de Taller 101 (`GET /licencias/llave`, kid `qjBcx7te`), en
#: hexadecimal. La privada la generó el Worker y vive en su base: ningún chat
#: la ve. Cambiar esta llave invalida todos los permisos emitidos: no se toca
#: sin rotar las dos y subir el `kid`.
LLAVE_PUBLICA = "c3f48035047675546eff0e88c522fddde8d18f526081b2c698bd8ad44846e409"
KID = "qjBcx7te"

#: A dónde se pide la activación y el latido.
SERVIDOR = "https://suite101-api.mike-929.workers.dev/licencias"
#: Este programa. El permiso dice para cuál se emitió: uno de nest101 no abre
#: draw101, aunque la llave sea la misma para los tres.
PROGRAMA = "draw101"

#: A partir de cuántos días por vencer se empieza a avisar.
AVISAR_DESDE = 7
ESPERA_RED = 12

#: Estados posibles, y lo que significan para quien usa el programa.
#:   activa      · suscripción al corriente
#:   por_vencer  · activa, pero quedan pocos días (se avisa sin estorbar)
#:   vencida     · el permiso caducó: modo lectura
#:   sin_activar · nunca se activó en esta máquina: modo lectura
ESTADOS_QUE_ESCRIBEN = {"activa", "por_vencer"}


def _archivo() -> pathlib.Path:
    return config.carpeta_usuario() / "licencia.json"


def huella_maquina() -> str:
    """Algo estable que identifique el equipo, sin identificar a la persona.

    Nombre del equipo, usuario de Windows y arquitectura, pasados por sha256:
    lo que viaja es el resumen, no los datos. Cambiar de computadora obliga a
    reactivar, que es justo lo que se quiere cobrar por máquina.
    """
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = "?"
    crudo = f"{platform.node()}|{usuario}|{platform.machine()}|{platform.system()}"
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


# --- El permiso firmado -----------------------------------------------------

def _b64url(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def leer_permiso(token: str) -> dict | None:
    """Abre un permiso y comprueba su firma. `None` si no cuadra.

    Formato del servidor: `v1.<carga>.<firma>`, las dos partes en base64url sin
    relleno. **La firma es sobre los bytes de la carga tal como llegan**: se
    verifica lo decodificado, nunca un JSON vuelto a serializar (reserializar
    cambia espacios y orden, y la firma dejaría de cuadrar por nada).
    """
    try:
        version, carga_b64, firma_b64 = token.strip().split(".")
        if version != "v1":
            return None
        carga = _b64url(carga_b64)
        rubrica = _b64url(firma_b64)
    except Exception:
        return None
    if not mod_firma.verificar(bytes.fromhex(LLAVE_PUBLICA), carga, rubrica):
        return None
    try:
        datos = json.loads(carga.decode("utf-8"))
    except Exception:
        return None
    if datos.get("programa") and datos["programa"] != PROGRAMA:
        return None                     # permiso de otro programa de la suite
    if datos.get("maquina") and datos["maquina"] != huella_maquina():
        return None                     # permiso de otra computadora
    return datos


def _hoy() -> dt.date:
    return dt.date.today()


def _fecha(s: str | None) -> dt.date | None:
    """El día de una fecha del servidor. Vienen en ISO con hora y zona
    («2026-10-18T02:40:11.000Z»); para decidir si se puede trabajar basta el
    día, y así no se pelea con la zona horaria de cada taller."""
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


# --- Lo que se guarda en disco ---------------------------------------------

def _guardado() -> dict:
    try:
        return json.loads(_archivo().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _guardar(datos: dict) -> None:
    try:
        _archivo().parent.mkdir(parents=True, exist_ok=True)
        _archivo().write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    except Exception:
        pass                            # sin permiso de escritura: no se cae


# --- El estado --------------------------------------------------------------

def estado() -> dict:
    """En qué situación está la licencia, ahora mismo y sin tocar la red."""
    datos = _guardado()
    permiso = leer_permiso(datos.get("token", "")) if datos.get("token") else None
    if not permiso:
        return _resumen("sin_activar", None, 0)

    hasta = _fecha(permiso.get("hasta"))
    faltan = (hasta - _hoy()).days if hasta else -1
    if faltan < 0:
        return _resumen("vencida", permiso, 0)
    nombre = "por_vencer" if faltan <= AVISAR_DESDE else "activa"
    return _resumen(nombre, permiso, faltan)


def _resumen(nombre: str, permiso: dict | None, faltan: int) -> dict:
    p = permiso or {}
    return {
        "estado": nombre,
        "puede_escribir": nombre in ESTADOS_QUE_ESCRIBEN,
        "dias": max(0, faltan),
        "cliente": p.get("cliente", ""),
        "plan": p.get("plan", ""),
        "licencia": p.get("licencia", ""),
        "hasta": p.get("hasta", ""),
        "mensaje": _mensaje(nombre, faltan),
    }


def _mensaje(nombre: str, faltan: int) -> str:
    if nombre == "activa":
        return ""
    if nombre == "por_vencer":
        return (f"La suscripción de draw101 vence en {faltan} día(s). "
                "Si ya está pagada, se renueva sola al abrir con internet.")
    if nombre == "vencida":
        return ("La suscripción venció: draw101 quedó en modo lectura. Se "
                "puede ver, medir e imprimir, pero no guardar ni exportar.")
    return ("draw101 no está activado en esta computadora: por ahora sólo "
            "lectura. Con una clave de suscripción se activa.")


def puede_escribir() -> bool:
    """¿Se puede guardar y exportar? Lo pregunta el servidor antes de hacerlo."""
    return estado()["puede_escribir"]


# --- Hablar con Taller 101 --------------------------------------------------

#: Lo que significa cada error del servidor, dicho para quien usa el programa.
MOTIVOS = {
    "datos_invalidos": "La clave no tiene la forma correcta (T101-XXXX-XXXX-XXXX).",
    "clave_inexistente": "Esa clave no existe. Revísala o pídela a Taller 101.",
    "sin_pago": "Esa licencia no está pagada o ya venció.",
    "suspendida": "Taller 101 suspendió esa licencia.",
    "sin_lugares": "Esa licencia ya está usada en todas sus computadoras. "
                   "Libera una desde otra máquina o pide más lugares.",
    "token_invalido": "El permiso guardado no sirve: hay que activar otra vez.",
    "maquina_desconocida": "Esta computadora ya no tiene lugar en la licencia: "
                           "hay que activarla otra vez.",
    "licencia_desconocida": "Esa licencia ya no existe.",
}


def _pedir(ruta: str, cuerpo: dict) -> dict:
    """Le habla al servidor y devuelve el `data` del sobre.

    Todo contesta `{"ok":true,"data":{…}}` o `{"ok":false,"error":"<código>"}`.
    Los códigos se traducen con MOTIVOS: quien usa draw101 no tiene por qué
    leer «sin_lugares».
    """
    pedido = urllib.request.Request(
        f"{SERVIDOR}{ruta}", method="POST",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "draw101"})
    try:
        with urllib.request.urlopen(pedido, timeout=ESPERA_RED) as r:
            sobre = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            sobre = json.loads(e.read().decode("utf-8"))
        except Exception:
            raise ValueError(f"El servidor contestó {e.code}.")
    except Exception as e:
        raise ValueError(f"No se pudo hablar con Taller 101: {e}")
    if not sobre.get("ok"):
        codigo = sobre.get("error", "")
        raise ValueError(MOTIVOS.get(codigo, f"El servidor dijo «{codigo}»."))
    return sobre.get("data") or {}


def activar(clave: str) -> dict:
    """Canjea la clave por un permiso firmado. Levanta ValueError si no cuadra."""
    from .version import VERSION
    datos = _pedir("/activar", {"clave": clave.strip().upper(),
                                "huella": huella_maquina(),
                                "version": VERSION})
    return _aceptar(datos)


def latido() -> dict:
    """Le pregunta al servidor si la suscripción sigue al corriente.

    Se llama una vez al día. **No levanta**: si no hay red, se queda como
    estaba y la fecha del permiso —que ya trae hasta 30 días de margen— hace su
    trabajo. Si el servidor dice que esta máquina ya no tiene lugar, se borra
    el permiso: lo honesto es pedir que se active otra vez, no seguir
    trabajando con uno que el dueño ya quitó.
    """
    from .version import VERSION
    guardado = _guardado()
    if not guardado.get("token"):
        return estado()
    try:
        datos = _pedir("/latido", {"token": guardado["token"],
                                   "huella": huella_maquina(),
                                   "version": VERSION})
        return _aceptar(datos)
    except ValueError as e:
        if any(x in str(e) for x in ("activar otra vez", "ya no existe")):
            guardado.pop("token", None)
            _guardar(guardado)
        return estado()
    except Exception:
        return estado()


def _aceptar(datos: dict) -> dict:
    """Guarda el permiso que contestó el servidor, si es de verdad."""
    token = (datos or {}).get("token", "")
    permiso = leer_permiso(token)
    if not permiso:
        raise ValueError("El permiso que contestó el servidor no es válido "
                         "para este programa o esta computadora.")
    guardado = _guardado()
    guardado.update({"token": token, "ultimo_latido": _hoy().isoformat(),
                     "cuando": time.time()})
    _guardar(guardado)
    return estado()


def desactivar() -> dict:
    """Suelta esta máquina: libera el lugar allá y borra el permiso de aquí."""
    guardado = _guardado()
    if guardado.get("token"):
        try:
            _pedir("/desactivar", {"token": guardado["token"],
                                   "huella": huella_maquina()})
        except Exception:
            pass                         # se suelta de este lado de todos modos
    guardado.pop("token", None)
    guardado.pop("ultimo_latido", None)
    _guardar(guardado)
    return estado()
