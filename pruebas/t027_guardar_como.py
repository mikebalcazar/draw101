"""t027 · «Guardar como…» también escribe DXF y DWG.

Mike (16-sep-2026): «en Save as… que aparezca la opción de DXF y DWG también,
aparte del botón de export».

Guardar en el formato propio (.t101d) guarda todo y renombra el dibujo; elegir
DXF o DWG es exportar: se escribe el archivo, se avisa de lo que no cupo y el
dibujo sigue llamándose como se llamaba (no se «convierte» en DXF a medias).

Se prueba con el diálogo de archivo simulado (en el navegador no hay Windows):
se comprueban los filtros que se ofrecen y lo que hace cada extensión.
"""

from __future__ import annotations

import pathlib
import tempfile

from pruebas import comun, navegador

DESCRIPCION = "Guardar como ofrece .t101d, DXF y DWG, y cada uno hace lo suyo"


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    carpeta = pathlib.Path(tempfile.mkdtemp())
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        navegador.comando(pagina, "RECTANGULO")
        navegador.comando(pagina, "0,0")
        navegador.comando(pagina, "500,300")
        pagina.keyboard.press("Escape")
        pagina.wait_for_timeout(200)

        # Los filtros que se ofrecen al guardar.
        f = pagina.evaluate("Archivo.filtrosGuardar().map((x) => x.extensions[0])")
        r.cierto(f[0] == "t101d", "el formato propio va primero")
        r.cierto("dxf" in f, "y se ofrece DXF")
        puede_dwg = pagina.evaluate("!!(estado.resumen.dwg || {}).puede")
        r.igual("dwg" in f, puede_dwg,
                "DWG se ofrece sólo si el conversor está instalado" if not puede_dwg
                else "y DWG, porque el conversor está instalado")

        # Guardar como .t101d: el dibujo pasa a vivir ahí.
        propio = str(carpeta / "mueble.t101d")
        ok = pagina.evaluate("""async (ruta) => {
            window.pedirRuta = async () => ruta;                 // el diálogo de Windows
            return await Archivo.guardar(true);
        }""", propio)
        pagina.wait_for_timeout(300)
        r.cierto(ok, "guardar como .t101d funciona")
        r.cierto(pathlib.Path(propio).is_file(), "y el archivo existe")
        r.cierto(pagina.evaluate("estado.resumen.ruta").endswith("mueble.t101d"),
                 "y el dibujo pasa a vivir en mueble.t101d")

        # Guardar como .dxf: se escribe el DXF y el dibujo NO se renombra.
        dxf = str(carpeta / "mueble.dxf")
        ok = pagina.evaluate("""async (ruta) => {
            window.pedirRuta = async () => ruta;
            return await Archivo.guardar(true);
        }""", dxf)
        pagina.wait_for_timeout(400)
        r.cierto(ok, "guardar como .dxf funciona")
        p = pathlib.Path(dxf)
        if r.cierto(p.is_file(), "y el DXF existe"):
            cabeza = p.read_text(errors="ignore")[:2000]
            r.cierto("SECTION" in cabeza, "con pinta de DXF de verdad")
        r.cierto(pagina.evaluate("estado.resumen.ruta").endswith("mueble.t101d"),
                 "y el dibujo sigue viviendo en mueble.t101d: exportar no es guardar")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
