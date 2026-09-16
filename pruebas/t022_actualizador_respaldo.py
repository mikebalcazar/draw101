"""t022 · El actualizador dice por qué falla, y tiene respaldo por Chromium.

Mike (15-sep-2026): «Nunca me avisa que hay nueva versión»; el cuadro decía
sólo «no se pudo consultar (¿sin internet?)» aunque los avisos del mismo sitio
sí llegaban. Dos cosas nuevas:

1. Cuando el motor no llega al puntero, guarda la razón exacta y la enseña.
2. La interfaz puede traer el puntero y el instalador con el motor de red de
   Chromium (fetch) y entregárselos al motor por dos rutas nuevas; el motor
   los interpreta, comprueba la huella y deja el instalador «listo», igual que
   si los hubiera bajado él.

Se prueba el motor directo (sin red: un puntero que no existe) y las rutas
por el servidor de pruebas (un instalador de mentira con su huella).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.request

from pruebas import comun, navegador

DESCRIPCION = "actualizador: la razón del fallo y el respaldo por Chromium"


def _post(base: str, ruta: str, datos: bytes, cabeceras: dict | None = None):
    req = urllib.request.Request(base + ruta, data=datos, method="POST",
                                 headers={"Content-Type": "application/json", **(cabeceras or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            return f.status, json.loads(f.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def correr(r: comun.Reporte) -> None:
    _motor_sin_red(r)
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: las rutas se saltan)")
        return
    _rutas(r)


def _motor_sin_red(r: comun.Reporte) -> None:
    from core import actualizar as a
    viejo = a.PUNTERO
    a.PUNTERO = "http://127.0.0.1:9/no-existe.json"          # puerto 9: nadie contesta
    a._ultima_revision.update({"cuando": 0.0, "datos": None, "error": ""})
    try:
        r.cierto(a._consultar(espera=1) is None, "sin red: la consulta devuelve None")
        res = a.resumen(con_red=True, forzar=True)
        r.cierto(not res["consulto"], "y el resumen dice que no se pudo consultar")
        r.cierto(bool(res["error"]), f"pero ahora dice POR QUÉ: {res['error'][:60]}")
        r.igual(res["puntero"], a.PUNTERO, "y cuál puntero intentó")

        # El respaldo: la interfaz entrega el puntero ya bajado.
        datos = {"draw101": {"version": "9.9.9", "fecha": "2026-09-15", "notas": ["prueba"],
                             "windows": {"archivo": "draw101-9.9.9-setup.exe", "bytes": 5, "sha256": hashlib.sha256(b"hola!").hexdigest(),
                                         "url": "https://ejemplo.invalido/x.exe"}}}
        ult = a.recibir_manifiesto(datos)
        r.igual(ult and ult["version"], "9.9.9", "el motor interpreta el puntero que le trajeron")
        res = a.resumen(con_red=True, forzar=False)
        r.cierto(res["consulto"] and res["hay_nueva"], "y ya hay versión nueva, sin error")
        r.igual(res["error"], "", "con la razón del fallo borrada")

        # El instalador entregado por la interfaz: huella buena y huella mala.
        e = a.recibir_archivo("draw101-9.9.9-setup.exe", b"hola!")
        r.igual(e["fase"], "listo", "el instalador que cuadra queda listo")
        r.cierto(e["ruta"].endswith("draw101-9.9.9-setup.exe"), "guardado con su nombre")
        try:
            a.recibir_archivo("draw101-9.9.9-setup.exe", b"otra cosa!")
            r.cierto(False, "un archivo que no cuadra debe rechazarse")
        except ValueError as exc:
            r.cierto("bytes" in str(exc) or "huella" in str(exc), f"un archivo que no cuadra se rechaza: {str(exc)[:50]}")
    finally:
        a.PUNTERO = viejo
        a._ultima_revision.update({"cuando": 0.0, "datos": None, "error": ""})
        a._poner("nada", 0, "")
        try:
            os.remove(os.path.join(a._carpeta_descargas(), "draw101-9.9.9-setup.exe"))
        except OSError:
            pass


def _rutas(r: comun.Reporte) -> None:
    with navegador.programa() as (pagina, base):
        cuerpo = b"instalador de mentira " * 1000
        datos = {"draw101": {"version": "9.9.8", "fecha": "2026-09-15", "notas": [],
                             "windows": {"archivo": "draw101-9.9.8-setup.exe", "bytes": len(cuerpo),
                                         "sha256": hashlib.sha256(cuerpo).hexdigest(), "url": "https://ejemplo.invalido/x.exe"}}}
        st, res = _post(base, "/api/actualizacion/manifiesto", json.dumps(datos).encode())
        r.igual(st, 200, "POST /api/actualizacion/manifiesto acepta un puntero")
        r.cierto(res.get("consulto") and res.get("hay_nueva"), "y el resumen ya dice que hay 9.9.8")
        st, res = _post(base, "/api/actualizacion/manifiesto", b"{}")
        r.igual(st, 400, "y rechaza uno sin versión")

        st, e = _post(base, "/api/actualizacion/recibir", cuerpo, {"Content-Type": "application/octet-stream", "X-Nombre": "draw101-9.9.8-setup.exe"})
        r.igual(st, 200, "POST /api/actualizacion/recibir acepta el instalador")
        r.igual(e.get("fase"), "listo", "y lo deja listo para instalar")
        st, e = _post(base, "/api/actualizacion/recibir", cuerpo[:-10], {"Content-Type": "application/octet-stream", "X-Nombre": "draw101-9.9.8-setup.exe"})
        r.igual(st, 400, "y rechaza uno incompleto")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
        try:
            from core import actualizar as a
            os.remove(os.path.join(a._carpeta_descargas(), "draw101-9.9.8-setup.exe"))
        except OSError:
            pass
