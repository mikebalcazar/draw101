"""t023 · La pantalla de inicio no se desborda con rutas largas.

Mike (15-sep-2026): «en la pantalla de inicio, las rutas de los docs se salen
completamente de la ventana. Sugiero que se abrevie». Dos causas y dos
arreglos: la rejilla usaba `1fr`, que no se encoge por debajo de su contenido
(ahora `minmax(0,1fr)`), y la ruta iba entera (ahora arranque + «…» + final,
con la ruta completa en el tooltip).

Se mete una ruta de 120 caracteres en los recientes, se abre el inicio y se
mide: la lista cabe en su columna, el renglón cabe en la lista, y el texto
lleva «…» con el arranque y el final de la ruta.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "inicio: rutas largas abreviadas y sin desbordar la ventana"

RUTA = ("G:\\Mi unidad\\taller101\\PROYECTOS taller 101\\FRANCISCO VIDAL\\Aniceto Ortega 1324"
        "\\NUEVO CLOSET\\Planta Aniceto Nuevo Piso copia.t101d")


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        pagina.evaluate("""(ruta) => {
            estado.prefs = estado.prefs || {};
            estado.prefs.recientes = [
                {nombre: 'Planta Aniceto Nuevo Piso', ruta, cuando: Date.now() - 2 * 86400000},
                {nombre: 'WP-MNDLZ-A100.dwg', ruta: 'C:\\\\Users\\\\mikeb\\\\Downloads\\\\WP-MNDLZ-A100.dwg', cuando: Date.now()},
            ];
            Marco.abrirInicio();
        }""", RUTA)
        pagina.wait_for_timeout(300)
        m = pagina.evaluate("""() => {
            const inicio = document.querySelector('#inicio');
            const cols = inicio.querySelector('.cols');
            const lista = inicio.querySelector('#iRecientes');
            const fila = lista.querySelector('.rec');
            const n2 = fila.querySelector('.n2');
            return {
                colsAncho: cols.getBoundingClientRect().width,
                ventana: window.innerWidth,
                listaAncho: lista.getBoundingClientRect().width,
                listaScroll: lista.scrollWidth,
                filaAncho: fila.getBoundingClientRect().width,
                texto: n2.textContent,
                tooltip: fila.title,
            };
        }""")
        r.cierto(m["colsAncho"] <= m["ventana"], f"las columnas caben en la ventana ({m['colsAncho']:.0f} ≤ {m['ventana']})")
        r.cierto(m["listaScroll"] <= m["listaAncho"] + 1, f"la lista no desborda su columna ({m['listaScroll']} ≤ {m['listaAncho']:.0f})")
        r.cierto(m["filaAncho"] <= m["listaAncho"] + 1, "cada renglón cabe en la lista")
        r.cierto("…" in m["texto"], "la ruta va abreviada con «…»")
        r.cierto(m["texto"].startswith("G:\\Mi unidad"), "conserva el arranque (unidad y primera carpeta)")
        r.cierto(m["texto"].endswith("Planta Aniceto Nuevo Piso copia.t101d"), "y el final (archivo)")
        r.cierto(len(m["texto"]) <= 70, f"y mide poco ({len(m['texto'])} caracteres)")
        r.igual(m["tooltip"], RUTA, "la ruta completa queda en el tooltip")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
"""
