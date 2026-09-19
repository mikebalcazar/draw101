"""t036 · La puerta de arranque y el motor hablan de la misma licencia.

Desde la 0.21.0 draw101 no abre sin licencia: antes del motor hay una puerta
en Electron (`electron/licencia.js`) que abre la pantalla de la suite —cuenta
con correo y contraseña o con Google, y abajo la clave T101-… para quien ya la
tenga— y guarda el permiso firmado que devuelva.

Eso deja **dos programas distintos tocando la misma licencia**: la puerta, en
JavaScript, y el motor, en Python. Si no coinciden en dónde guardan y en cómo
llaman a este equipo, pasa lo peor posible: la puerta deja entrar y adentro la
app dice «sin activar» y no deja guardar. No truena, no avisa: miente. Por eso
esta prueba existe y por eso compara los dos lados de verdad, corriendo node.

Lo que se comprueba:

  · Los dos usan **la misma carpeta** (`~/Taller 101/draw101`).
  · Los dos sacan **la misma huella** del mismo `equipo.json`, la escriba quien
    la escriba. (Se cazó el 19-sep-2026: la puerta guardaba en
    `%APPDATA%/draw101` con un azar, y el motor calculaba un resumen de
    nombre+usuario+arquitectura en otra carpeta. Ninguno de los dos estaba
    mal por su cuenta; juntos no servían.)
  · El `licencia.json` que escribe la puerta **lo entiende el motor**, y el
    motor no le borra lo que la puerta puso (`hasta`, `licencia`, `correo`).
  · Y se corre la prueba del núcleo de la puerta (`pruebas/licencia.mjs`, de
    Jr.), que mide lo suyo: la forma de la huella, lo que sobrevive entre
    arranques, abrir sin internet mientras el token no venza, y —lo que más
    importa— que «la suite dice que no» y «no se pudo llegar a la suite» no se
    confundan.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile

from pruebas import comun

NOMBRE = "t036"
DESCRIPCION = "la puerta de arranque y el motor, de acuerdo sobre la misma licencia"

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _hay_node() -> str | None:
    return shutil.which("node")


def correr(r: comun.Reporte) -> None:
    node = _hay_node()
    if not node:
        r.cierto(True, "sin node no se puede medir la puerta: se salta")
        return
    _misma_carpeta(r)
    _misma_huella(r, node)
    _mismo_archivo(r, node)
    _nucleo_de_la_puerta(r, node)


def _misma_carpeta(r: comun.Reporte) -> None:
    """La puerta dice en JavaScript dónde guarda; el motor, en Python. Tienen
    que dar lo mismo, y aquí se comparan las dos respuestas, no un comentario."""
    from core import config
    del config                                   # sólo para fallar pronto si no importa

    js = (RAIZ / "electron" / "licencia.js").read_text(encoding="utf-8")
    r.cierto('path.join(os.homedir(), "Taller 101", "draw101")' in js,
             "la puerta guarda en ~/Taller 101/draw101, no en la carpeta de Electron")
    # Se miran sólo los renglones de código: el comentario de arriba nombra la
    # carpeta vieja a propósito, para que se entienda por qué no se usa.
    codigo = "\n".join(l for l in js.splitlines()
                       if not l.lstrip().startswith(("*", "/*", "//")))
    r.cierto("app.getPath" not in codigo,
             "y ya no queda una llamada a la carpeta de Electron, que era el desacuerdo")


def _huella_python(carpeta: pathlib.Path) -> str:
    from core import config, licencia
    viejo = config.carpeta_usuario
    config.carpeta_usuario = lambda: carpeta                  # type: ignore
    try:
        return licencia.huella_maquina()
    finally:
        config.carpeta_usuario = viejo                        # type: ignore


def _huella_node(node: str, carpeta: pathlib.Path) -> str:
    salida = subprocess.run(
        [node, "-e",
         "const n=require('./electron/licencia-nucleo.js');"
         f"process.stdout.write(n.huella({json.dumps(str(carpeta))}))"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=60)
    return salida.stdout.strip()


def _misma_huella(r: comun.Reporte, node: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = pathlib.Path(tmp)
        de_node = _huella_node(node, carpeta)
        de_python = _huella_python(carpeta)
        r.igual(de_python, de_node,
                "la huella que escribe la puerta es la que lee el motor")

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = pathlib.Path(tmp)
        de_python = _huella_python(carpeta)
        de_node = _huella_node(node, carpeta)
        r.igual(de_node, de_python,
                "y al revés: la que escribe el motor es la que lee la puerta")

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = pathlib.Path(tmp)
        h = _huella_python(carpeta)
        r.cierto(len(h) >= 16 and all(c.isalnum() or c in "-_" for c in h),
                 "tiene la forma que la suite acepta", f"{len(h)} caracteres")
        r.igual(_huella_python(carpeta), h,
                "y no cambia en el siguiente arranque: no gasta un lugar nuevo cada vez")
        # Que no lleve dentro el nombre del equipo es lo que la hace no
        # identificar a nadie; el azar es lo que la hace irreversible.
        import platform
        r.cierto(platform.node() not in h, "no lleva dentro el nombre del equipo")
        with tempfile.TemporaryDirectory() as otro:
            r.cierto(_huella_python(pathlib.Path(otro)) != h,
                     "y otra instalación es otro equipo")


def _mismo_archivo(r: comun.Reporte, node: str) -> None:
    """Lo que la puerta guarda al activar tiene que servirle al motor tal cual,
    y el motor no debe pisarle lo suyo al escribir encima."""
    from core import config, licencia
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = pathlib.Path(tmp)
        subprocess.run(
            [node, "-e",
             "const n=require('./electron/licencia-nucleo.js');"
             f"n.guardar({json.dumps(str(carpeta))}, "
             "{token:'v1.carga.firma', hasta:'2099-12-31T00:00:00Z',"
             " licencia:'L-1', correo:'alguien@ejemplo.mx'})"],
            cwd=str(RAIZ), capture_output=True, text=True, timeout=60)

        viejo = config.carpeta_usuario
        config.carpeta_usuario = lambda: carpeta               # type: ignore
        try:
            guardado = licencia._guardado()
            r.igual(guardado.get("token"), "v1.carga.firma",
                    "el motor lee el permiso que dejó la puerta")
            r.igual(guardado.get("correo"), "alguien@ejemplo.mx",
                    "y ve de qué cuenta salió")
            # El motor vuelve a escribir el archivo en cada latido: no puede
            # perder lo que la puerta puso, o la puerta dejaría de saber hasta
            # cuándo vale sin preguntar.
            licencia._guardar({**guardado, "ultimo_latido": "2026-09-19"})
            despues = json.loads((carpeta / "licencia.json").read_text(encoding="utf-8"))
            r.igual(despues.get("hasta"), "2099-12-31T00:00:00Z",
                    "y al escribir encima no le borra la fecha a la puerta")
            r.igual(despues.get("licencia"), "L-1", "ni cuál licencia es")
        finally:
            config.carpeta_usuario = viejo                     # type: ignore


def _nucleo_de_la_puerta(r: comun.Reporte, node: str) -> None:
    """La prueba de Jr. para el núcleo de la puerta, corrida aquí para que
    entre en cada armado junto con las demás."""
    prueba = RAIZ / "pruebas" / "licencia.mjs"
    if not prueba.exists():
        r.cierto(False, "pruebas/licencia.mjs debería existir: es la prueba de la puerta")
        return
    salida = subprocess.run([node, str(prueba)], cwd=str(RAIZ),
                            capture_output=True, text=True, timeout=180)
    cuantas = salida.stdout.count("  ok   ")
    r.cierto(salida.returncode == 0,
             "el núcleo de la puerta pasa sus 20 comprobaciones",
             (salida.stdout + salida.stderr)[-400:])
    r.cierto(cuantas >= 20,
             f"y se corrieron todas ({cuantas} comprobaciones)")
