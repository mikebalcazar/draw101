"""t035 · La suscripción, vista desde la app.

t033 cubre el motor —la firma, la huella, el vencimiento—. Ésta cubre lo que
ve quien usa draw101, que es lo que puede costar un cliente enojado:

  · Al arrancar sin licencia sale la **pantalla de activación**, una vez por
    sesión, y se puede seguir sin activar.
  · Una clave buena **activa** de verdad: el motor guarda el permiso firmado y
    el panel pasa a decir «Al corriente» con el cliente y la fecha.
  · Una clave mala enseña **el motivo del servidor**, no «Error 402».
  · El comando `LICENCIA` abre el panel, y de ahí se **suelta** la máquina.
  · El **latido** corre la fecha de corte sola.
  · Con el corte **apagado** (0.20.20, como se publica) guardar y exportar
    funcionan sin licencia: es lo que Mike decidió el 19-sep-2026 y hay que
    dejarlo clavado, porque encenderlo antes de tiempo deja a un taller sin
    poder guardar.
  · Con el corte **encendido** (lo que será la 0.20.21) guardar y exportar
    contestan 402 con el motivo, el autoguardado se calla, e **imprimir sigue
    funcionando**: quien ya pagó por el plano tiene derecho a verlo y
    sacarlo en papel.

El servidor de licencias aquí es de mentira —se firma con una llave que esta
prueba se inventa— porque la prueba no puede depender de que suite101-api esté
arriba ni gastar claves de verdad. Lo que se comprueba es que draw101 hable
bien con lo que ese servidor contesta.
"""

from __future__ import annotations

import base64
import datetime as dt
import http.server
import json
import pathlib
import tempfile
import threading
import urllib.error
import urllib.request

from pruebas import comun

NOMBRE = "t035"
DESCRIPCION = "la suscripción vista desde la app: activar, panel, latido y el corte"


def _hay_cryptography() -> bool:
    try:
        import cryptography  # noqa: F401
        return True
    except Exception:
        return False


# --- El servidor de licencias de mentira ------------------------------------

class Taller101Falso:
    """Habla como suite101-api 0.13.0 y firma con una llave inventada.

    Guarda el sobre `{"ok":…}` igual que el de verdad, contesta los mismos
    códigos de error y liga el permiso a la huella que le manden. Lo que no
    hace es cobrar: aquí `CLAVE_BUENA` está pagada y ya.
    """

    CLAVE_BUENA = "T101-AAAA-BBBB-CCCC"

    def __init__(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        self._priv = Ed25519PrivateKey.generate()
        self.publica = self._priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw).hex()
        self.dias = 30
        self.maquinas: set[str] = set()
        self.lugares = 1
        self.latidos = 0
        self.puerto = 0
        self._httpd = None
        self._hilo = None

    # -- el permiso ---------------------------------------------------------

    def _b64(self, b: bytes) -> str:
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    def token(self, huella: str, programa: str = "draw101") -> str:
        hasta = dt.datetime.utcnow() + dt.timedelta(days=self.dias)
        carga = json.dumps({
            "v": 1, "kid": "prueba", "programa": programa,
            "licencia": "L-PRUEBA", "cliente": "Carpintería Ruiz",
            "plan": "mensual", "lugares": self.lugares, "maquina": huella,
            "emitido": dt.datetime.utcnow().isoformat() + "Z",
            "hasta": hasta.isoformat() + "Z",
        }, ensure_ascii=False).encode("utf-8")
        return f"v1.{self._b64(carga)}.{self._b64(self._priv.sign(carga))}"

    # -- las rutas ----------------------------------------------------------

    def _responder(self, ruta: str, cuerpo: dict) -> tuple[int, dict]:
        huella = cuerpo.get("huella", "")
        if ruta.endswith("/activar"):
            if cuerpo.get("clave") != self.CLAVE_BUENA:
                return 404, {"ok": False, "error": "clave_inexistente"}
            if huella not in self.maquinas and len(self.maquinas) >= self.lugares:
                return 409, {"ok": False, "error": "sin_lugares"}
            self.maquinas.add(huella)
            return 201, {"ok": True, "data": {"token": self.token(huella)}}
        if ruta.endswith("/latido"):
            if huella not in self.maquinas:
                return 403, {"ok": False, "error": "maquina_desconocida"}
            self.latidos += 1
            return 200, {"ok": True, "data": {"token": self.token(huella)}}
        if ruta.endswith("/desactivar"):
            self.maquinas.discard(huella)
            return 200, {"ok": True, "data": {"liberada": True}}
        return 404, {"ok": False, "error": "no_existe"}

    def arrancar(self) -> str:
        falso = self

        class Manejador(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                largo = int(self.headers.get("Content-Length") or 0)
                try:
                    cuerpo = json.loads(self.rfile.read(largo).decode("utf-8"))
                except Exception:
                    cuerpo = {}
                codigo, sobre = falso._responder(self.path, cuerpo)
                datos = json.dumps(sobre).encode("utf-8")
                self.send_response(codigo)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(datos)))
                self.end_headers()
                self.wfile.write(datos)

            def log_message(self, *a):
                pass                      # sin ruido en la corrida

        self._httpd = http.server.HTTPServer(("127.0.0.1", 0), Manejador)
        self.puerto = self._httpd.server_address[1]
        self._hilo = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._hilo.start()
        return f"http://127.0.0.1:{self.puerto}/licencias"

    def parar(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()


# --- La prueba ---------------------------------------------------------------

def correr(r: comun.Reporte) -> None:
    # El corte va primero y sin condiciones: no necesita firmar nada, y es la
    # comprobación que de verdad protege —que la versión publicada no deje a un
    # taller sin poder guardar—. En el corredor, donde no hay `cryptography` ni
    # navegador, ésta es la única que corre, y es la que tiene que correr.
    _corte_encendido(r)
    if not _hay_cryptography():
        r.cierto(True, "sin `cryptography` no se puede firmar: el resto se salta",
                 "pip install cryptography")
        return
    _motor(r)
    _interfaz(r)


def _apuntar_a(falso, carpeta):
    """Deja el motor de licencias hablando con el servidor de mentira y
    guardando en una carpeta de usar y tirar. Devuelve cómo se deshace."""
    from core import config, licencia
    viejos = (licencia.SERVIDOR, licencia.LLAVE_PUBLICA, licencia.CORTA,
              config.carpeta_usuario)
    licencia.SERVIDOR = falso.arrancar()
    licencia.LLAVE_PUBLICA = falso.publica
    config.carpeta_usuario = lambda: carpeta               # type: ignore

    def deshacer():
        (licencia.SERVIDOR, licencia.LLAVE_PUBLICA, licencia.CORTA,
         config.carpeta_usuario) = viejos                  # type: ignore
        falso.parar()
    return deshacer


def _motor(r: comun.Reporte) -> None:
    """Lo que hace el motor cuando habla con un servidor de verdad: activar,
    latir, soltar, y el corte encendido y apagado."""
    from core import licencia
    falso = Taller101Falso()
    with tempfile.TemporaryDirectory() as tmp:
        deshacer = _apuntar_a(falso, pathlib.Path(tmp))
        try:
            r.igual(licencia.estado()["estado"], "sin_activar",
                    "recién instalado, draw101 está sin activar")
            r.cierto(licencia.puede_escribir(),
                     "y con el corte apagado (0.20.20) igual se puede guardar")

            # Una clave que no existe: el motivo se dice en cristiano.
            try:
                licencia.activar("T101-XXXX-XXXX-XXXX")
                r.cierto(False, "una clave inexistente no activa")
            except ValueError as e:
                r.cierto("no existe" in str(e).lower(),
                         "una clave inexistente falla diciendo por qué",
                         str(e))

            # La buena sí.
            e = licencia.activar(Taller101Falso.CLAVE_BUENA)
            r.igual(e["estado"], "activa", "con la clave buena queda activa")
            r.igual(e["cliente"], "Carpintería Ruiz", "y dice de quién es")
            r.cierto(e["licencia_al_corriente"], "la suscripción está al corriente")

            # El latido corre la fecha.
            falso.dias = 45
            antes = licencia.estado()["hasta"]
            licencia.latido()
            r.cierto(licencia.estado()["hasta"] > antes,
                     "el latido corre la fecha de corte cuando el pago sigue al día")
            r.igual(falso.latidos, 1, "y se pidió una sola vez")

            # Por vencer avisa sin estorbar.
            falso.dias = 3
            licencia.latido()
            e = licencia.estado()
            r.igual(e["estado"], "por_vencer", "a tres días avisa que está por vencer")
            r.cierto(e["puede_escribir"], "pero deja trabajar: todavía está pagada")

            # El corte encendido es lo único que separa esto de la versión que cobra.
            falso.dias = -1
            licencia.latido()
            licencia.CORTA = False
            r.cierto(licencia.puede_escribir(),
                     "vencida y con el corte apagado, se sigue pudiendo guardar")
            r.igual(licencia.motivo_para_no_escribir(), "",
                    "y el motor no da motivo para negarse")
            licencia.CORTA = True
            r.cierto(not licencia.puede_escribir(),
                     "vencida y con el corte encendido, ya no se guarda")
            r.cierto("venci" in licencia.motivo_para_no_escribir().lower(),
                     "y el motivo dice que venció",
                     licencia.motivo_para_no_escribir())
            licencia.CORTA = False

            # Soltar la máquina libera el lugar allá y deja esto sin activar.
            falso.dias = 30
            licencia.activar(Taller101Falso.CLAVE_BUENA)
            licencia.desactivar()
            r.igual(licencia.estado()["estado"], "sin_activar",
                    "al soltar la computadora, draw101 queda sin activar aquí")
            r.igual(len(falso.maquinas), 0, "y el lugar queda libre en el servidor")
        finally:
            deshacer()


def _motor_aparte(entorno: dict):
    """Arranca el motor solo —sin navegador— en un puerto libre.

    Se necesita porque el corte se decide **al importar** `core.licencia`, y
    eso pasa en el proceso del motor: encenderlo desde aquí no lo tocaría.
    La salida se manda a la basura a propósito: dejarla en una tubería que
    nadie vacía cuelga el motor cuando escribe unos cuantos kilobytes.
    """
    import os
    import socket
    import subprocess
    import sys
    import time

    s = socket.socket(); s.bind(("127.0.0.1", 0)); puerto = s.getsockname()[1]; s.close()
    raiz = pathlib.Path(__file__).resolve().parent.parent
    motor = subprocess.Popen(
        [sys.executable, str(raiz / "server.py"), str(puerto)], cwd=str(raiz),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, **entorno})
    base = f"http://127.0.0.1:{puerto}"
    for _ in range(120):
        try:
            urllib.request.urlopen(base + "/api/salud", timeout=1)
            return motor, base
        except Exception:
            if motor.poll() is not None:
                raise RuntimeError("el motor no arrancó con el corte encendido")
            time.sleep(0.25)
    motor.kill()
    raise RuntimeError("el motor no contestó a /api/salud")


def _pedir(base: str, ruta: str, cuerpo: dict | None = None):
    """Devuelve `(codigo, datos)`. Un 402 no es una excepción aquí: es la
    respuesta que se está comprobando."""
    datos = json.dumps(cuerpo or {}).encode("utf-8")
    pedido = urllib.request.Request(base + ruta, data=datos, method="POST",
                                    headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}


def _corte_encendido(r: comun.Reporte) -> None:
    """Cómo va a quedar la 0.20.21: sin licencia no se escribe.

    Vale la pena probarlo ahora, con el corte apagado en la versión que se
    publica: el día que se encienda no habrá que averiguar si funciona, ya se
    sabrá. Y si alguien lo enciende por error, estas comprobaciones dicen
    exactamente qué deja de poderse.
    """
    with tempfile.TemporaryDirectory() as tmp:
        motor, base = _motor_aparte({
            "DRAW101_CORTA": "1",
            "DRAW101_OFRECER_ACTIVACION": "0",
            "HOME": tmp, "USERPROFILE": tmp,
        })
        try:
            with urllib.request.urlopen(base + "/api/licencia", timeout=10) as resp:
                e = json.loads(resp.read().decode("utf-8"))
            r.cierto(e["corta"], "con DRAW101_CORTA=1 el motor arranca cortando")
            r.cierto(not e["puede_escribir"], "y sin licencia no deja escribir")

            codigo, datos = _pedir(base, "/api/guardar",
                                   {"ruta": str(pathlib.Path(tmp) / "x.t101d")})
            r.igual(codigo, 402, "guardar sin licencia contesta 402, no 500 ni un guardado a medias")
            r.cierto("activad" in (datos.get("detail") or "").lower(),
                     "y dice que hay que activar, no «Error 402»",
                     str(datos)[:90])
            r.cierto(not (pathlib.Path(tmp) / "x.t101d").exists(),
                     "y no dejó el archivo escrito a medias")

            codigo, datos = _pedir(base, "/api/exportar_dxf",
                                   {"ruta": str(pathlib.Path(tmp) / "x.dxf")})
            r.igual(codigo, 402, "exportar sin licencia también se corta")
            r.cierto(not (pathlib.Path(tmp) / "x.dxf").exists(), "y tampoco escribe el DXF")

            codigo, datos = _pedir(base, "/api/autoguardar")
            r.igual(codigo, 200, "el autoguardado no grita: corre solo y nadie lo pidió")
            r.cierto(datos.get("sin_licencia"), "pero dice que no guardó por falta de licencia")

            # Lo que **sí** se puede: ver y medir. Quien ya pagó por el plano
            # tiene derecho a abrirlo aunque se le haya vencido el mes.
            with urllib.request.urlopen(base + "/api/estado", timeout=10) as resp:
                r.igual(resp.status, 200, "ver el dibujo sigue funcionando sin licencia")
        finally:
            motor.terminate()
            try:
                motor.wait(timeout=5)
            except Exception:
                motor.kill()


def _interfaz(r: comun.Reporte) -> None:
    """Lo mismo, pero picando botones: es donde se rompen estas cosas."""
    from pruebas import navegador as nav
    if not nav.hay_navegador():
        r.cierto(True, "sin Playwright no se prueba la interfaz: se salta")
        return

    from core import config, licencia
    falso = Taller101Falso()
    servidor = falso.arrancar()
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = pathlib.Path(tmp)
        # El motor corre en **otro proceso** (navegador.app lo arranca), así
        # que la configuración se le pasa por el ambiente, no tocando módulos.
        entorno = {
            "DRAW101_LICENCIA_SERVIDOR": servidor,
            "DRAW101_LICENCIA_LLAVE": falso.publica,
            "HOME": str(carpeta),
            "USERPROFILE": str(carpeta),
            # navegador.py la apaga para todas las pruebas (taparía el
            # lienzo); ésta es justamente la que tiene que verla.
            "DRAW101_OFRECER_ACTIVACION": "1",
        }
        try:
            with nav.programa(entorno=entorno) as (pagina, base):
                pagina.evaluate("Licencia.temporizadores.forEach(clearTimeout)")

                # 0. La pantalla de activación sale sola al arrancar sin
                # licencia, y se puede seguir sin activar.
                pagina.evaluate("() => { Licencia.revisar(); }")
                pagina.wait_for_selector(".dlg", timeout=8000)
                bienvenida = pagina.locator(".dlg .panel").inner_text()
                r.cierto("draw101" in bienvenida,
                         "al arrancar sin licencia sale sola la pantalla de activación",
                         bienvenida[:80])
                r.cierto(pagina.locator('.dlg input[data-clave="clave"]').count() == 1,
                         "con un solo campo: la clave")
                pagina.click(".dlg .pie button:not(.pri)")      # «Ahora no»
                pagina.wait_for_timeout(400)
                r.cierto(not pagina.locator(".dlg").count(),
                         "y se puede seguir sin activar: el cuadro no atrapa")
                pagina.evaluate("() => { Licencia.revisar(); }")
                pagina.wait_for_timeout(600)
                r.cierto(not pagina.locator(".dlg").count(),
                         "y no vuelve a salir en la misma sesión: se ofrece una vez, no cada rato")

                # 1. El estado que ve la interfaz es el del motor.
                e = pagina.evaluate("fetch('/api/licencia').then((r) => r.json())")
                r.igual(e["estado"], "sin_activar",
                        "la app recién abierta se ve sin activar")
                r.cierto(e["puede_escribir"],
                         "y con el corte apagado la app sabe que sí se puede guardar")
                r.cierto(not e["corta"],
                         "la 0.20.20 sale con el corte apagado (Mike, 19-sep-2026)")

                # 2. Sin corte no se apagan los botones: apagar algo que
                # funciona es mentir al revés.
                nav.cerrar_inicio(pagina)
                r.cierto(not pagina.locator("#b-guardar").is_disabled(),
                         "con el corte apagado, el botón de guardar sigue vivo")
                r.cierto(not pagina.locator("#marca-lectura").count(),
                         "y no aparece la marca de «modo lectura»")

                # 3. El comando LICENCIA abre el panel y dice la verdad.
                nav.comando(pagina, "LICENCIA")
                pagina.wait_for_selector(".dlg", timeout=5000)
                texto = pagina.locator(".dlg .panel").inner_text()
                r.cierto("Sin activar" in texto or "Not activated" in texto,
                         "el panel dice que está sin activar", texto[:80])
                r.cierto("no corta" in texto or "does not cut" in texto,
                         "y avisa de que por ahora no corta", texto[:120])

                # 4. Activar desde ahí, con la clave buena.
                pagina.click(".dlg .pie button.pri")        # «Activar…»
                pagina.wait_for_selector('.dlg input[data-clave="clave"]', timeout=5000)
                pagina.fill('.dlg input[data-clave="clave"]', Taller101Falso.CLAVE_BUENA)
                pagina.click(".dlg .pie button.pri")
                pagina.wait_for_timeout(1200)
                e = pagina.evaluate("fetch('/api/licencia').then((r) => r.json())")
                r.igual(e["estado"], "activa", "activar desde la app deja la licencia activa")
                r.igual(e["cliente"], "Carpintería Ruiz", "con el cliente que dijo el servidor")
                r.igual(len(falso.maquinas), 1, "y el servidor apuntó esta máquina")

                # 5. El panel ya dice otra cosa, y ofrece soltar.
                nav.comando(pagina, "LICENCIA")
                pagina.wait_for_selector(".dlg", timeout=5000)
                texto = pagina.locator(".dlg .panel").inner_text()
                r.cierto("Al corriente" in texto or "Up to date" in texto,
                         "el panel pasa a decir que está al corriente", texto[:80])
                r.cierto("Carpintería Ruiz" in texto, "y de quién es la suscripción")
                pagina.keyboard.press("Escape")

                # 6. El latido, pedido a mano como lo pide el arranque.
                pagina.evaluate("Licencia.latido()")
                pagina.wait_for_timeout(800)
                r.cierto(falso.latidos >= 1, "el latido llega al servidor")

                r.igual(pagina.errores, [], "sin errores de JavaScript")
        finally:
            falso.parar()
