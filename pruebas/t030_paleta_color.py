"""t030 · Paleta de colores y selector RGB.

Mike (16-sep-2026): «cuando quiero cambiar de color en las propiedades de un
layer o de una entidad, sólo me salen códigos de color. Implementa una paleta
de colores predeterminados y un selector de RGB o algo así».

Antes: en la entidad, una lista con los códigos de los colores que ya usaban
las capas («#808080»); en la capa, el cuadrito de Windows. Ahora los dos abren
la misma paleta: los nueve del índice de AutoCAD, los de Taller 101, grises,
los que ya usa el dibujo, el selector del sistema (RGB) y la caja del código.

Se comprueba en el navegador, picando de verdad.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "paleta de colores y RGB, en capa y en entidad"


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        _paleta(r, pagina)
        _capa(r, pagina, base)
        _entidad(r, pagina, base)
        r.igual(pagina.errores, [], "sin errores de JavaScript")


def _paleta(r: comun.Reporte, pagina) -> None:
    m = pagina.evaluate("""() => {
        const b = document.createElement('button');
        document.body.appendChild(b);
        const caja = Color.abrir(b, '#808080', {porCapa: true});
        const muestras = [...caja.querySelectorAll('.muestra')];
        const res = {
            muestras: muestras.length,
            titulos: [...caja.querySelectorAll('.tit')].map((t) => t.textContent),
            elegida: muestras.filter((x) => x.classList.contains('on')).length,
            rgb: !!caja.querySelector('input[type=color]'),
            codigo: caja.querySelector('.codigo') ? caja.querySelector('.codigo').value : null,
            porCapa: !!caja.querySelector('.porcapa'),
            dentro: (() => { const c = caja.getBoundingClientRect();
                return c.left >= 0 && c.top >= 0 && c.right <= innerWidth && c.bottom <= innerHeight; })(),
        };
        Color.cerrar(); b.remove();
        return res;
    }""")
    r.cierto(m["muestras"] >= 20, f"la paleta trae sus colores ({m['muestras']} muestras)")
    r.cierto(len(m["titulos"]) >= 3, f"agrupados ({m['titulos']})")
    r.igual(m["elegida"], 1, "y el color actual sale marcado")
    r.cierto(m["rgb"], "hay selector RGB (el del sistema)")
    r.igual(m["codigo"], "#808080", "y la caja del código, con el color puesto")
    r.cierto(m["porCapa"], "con «Por capa» cuando aplica")
    r.cierto(m["dentro"], "y la paleta cabe en la ventana")

    # El código se limpia y se entiende en varias formas.
    hexes = pagina.evaluate("['#abc', 'ABCDEF', '#00ff00', 'xyz'].map((x) => Color.hex(x))")
    r.igual(hexes, ["#AABBCC", "#ABCDEF", "#00FF00", None], "el código admite #abc, sin # y en minúsculas; lo que no es color, no")


def _capa(r: comun.Reporte, pagina, base) -> None:
    """La capa 0: picar la muestra abre la paleta; elegir un color lo guarda."""
    # El panel de propiedades de capa es flotante: lo abre PropsCapa.
    pagina.evaluate("document.querySelector('#capas .capa').click()")
    pagina.evaluate("PropsCapa.abrir(300, 200)")
    pagina.wait_for_timeout(300)
    r.cierto(not pagina.evaluate("document.querySelector('#props').hidden"),
             "las propiedades de la capa están abiertas")
    pagina.click("#p-color")
    pagina.wait_for_timeout(200)
    r.cierto(pagina.evaluate("!!document.querySelector('.paleta')"),
             "picar el color de la capa abre la paleta")
    pagina.evaluate("""() => [...document.querySelectorAll('.paleta .muestra')]
        .find((b) => b.title.includes('rojo')).click()""")
    pagina.wait_for_timeout(500)
    color = pagina.evaluate("(estado.resumen.capas.find((c) => c.nombre === '0') || {}).color")
    r.igual(color, "#FF0000", "y elegir el rojo cambia el color de la capa")
    r.cierto(not pagina.evaluate("document.querySelector('#props').hidden"),
             "y las propiedades siguen abiertas: elegir color no las cierra")
    r.cierto(not pagina.evaluate("!!document.querySelector('.paleta')"), "la paleta se cierra al elegir")


def _entidad(r: comun.Reporte, pagina, base) -> None:
    """Una línea seleccionada: su color ya no es una lista de códigos."""
    navegador.comando(pagina, "LINEA")
    navegador.comando(pagina, "0,0")
    navegador.comando(pagina, "100,0")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)
    ids = pagina.evaluate("estado.trazos.map((t) => t.id)")
    pagina.evaluate("(ids) => { estado.sel.clear(); ids.forEach((i) => estado.sel.add(i)); }", ids)

    m = pagina.evaluate("""() => {
        const b = selectorColor('');
        document.body.appendChild(b);
        const antes = {etiqueta: b.className, valor: b.value, esLista: b.tagName === 'SELECT'};
        b.click();
        const caja = document.querySelector('.paleta');
        const hay = !!caja;
        if (caja) [...caja.querySelectorAll('.muestra')].find((x) => x.title.includes('azul')).click();
        const despues = b.value;
        b.remove(); Color.cerrar();
        return {...antes, hay, despues};
    }""")
    r.cierto(not m["esLista"], "el color de la entidad ya no es una lista de códigos")
    r.igual(m["valor"], "", "arranca en «Por capa» cuando no tiene color propio")
    r.cierto(m["hay"], "picarlo abre la paleta")
    r.igual(m["despues"], "#0000FF", "y elegir el azul deja el color en el control")
