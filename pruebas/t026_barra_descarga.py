"""t026 · La barra de progreso de la descarga.

Mike (16-sep-2026): «hay que hacer una barrita de progreso de cuando se está
descargando la nueva versión de draw101, con diseño bonito». Antes sólo había
un renglón de texto que se reescribía con los megas.

Se comprueba lo que se puede medir sin ojos: que aparezca, que el relleno
crezca con el avance, que se ponga en modo «no sé cuánto falta» cuando el
servidor no dice el total, que al terminar se ponga verde y se cierre sola, y
que al fallar se ponga roja. También que quepa en la ventana y que no tape la
consola.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "la barra de progreso de la descarga: avance, fin y fallo"


def _estado(pagina):
    return pagina.evaluate("""() => {
        const c = document.getElementById('barra-descarga');
        if (!c) return null;
        const r = c.getBoundingClientRect();
        const rel = c.querySelector('.relleno');
        return {
            visible: c.classList.contains('si'),
            indet: c.classList.contains('indet'),
            fin: c.classList.contains('fin'),
            mal: c.classList.contains('mal'),
            titulo: c.querySelector('.tit').textContent,
            izq: c.querySelector('.pie span').textContent,
            der: c.querySelectorAll('.pie span')[1].textContent,
            ancho: rel.style.width,
            dentro: r.left >= 0 && r.right <= window.innerWidth && r.top >= 0,
            alto: r.height,
        };
    }""")


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        B = "Actualizar.Barra"

        r.igual(_estado(pagina), None, "sin descarga, la barra ni existe")

        pagina.evaluate(f"{B}.mostrar({{titulo: 'Bajando draw101 9.9.9…', pct: 0, ya: 0, total: 124000000}})")
        e = _estado(pagina)
        r.cierto(e and e["visible"], "al empezar la descarga, la barra aparece")
        r.cierto("9.9.9" in e["titulo"], "con la versión en el título")
        r.igual(e["ancho"], "0%", "el relleno arranca en cero")
        r.igual(e["der"], "0 %", "y el porcentaje también")
        r.cierto("124 MB" in e["izq"], f"con los megas totales ({e['izq']})")
        r.cierto(e["dentro"], "cabe en la ventana")

        pagina.evaluate(f"{B}.mostrar({{titulo: 'Bajando draw101 9.9.9…', pct: 42.7, ya: 53000000, total: 124000000}})")
        e = _estado(pagina)
        r.igual(e["ancho"], "42.7%", "el relleno crece con el avance")
        r.igual(e["der"], "43 %", "el porcentaje va redondeado")
        r.cierto("53.0 de 124 MB" in e["izq"], f"y los megas, bajados de totales ({e['izq']})")
        r.cierto(not e["indet"], "sabiendo el total, la barra no corre sola")

        # Sin total (servidor que no lo dice): barra corriendo, sin porcentaje.
        pagina.evaluate(f"{B}.mostrar({{titulo: 'Bajando…', pct: null, ya: 9000000, total: 0}})")
        e = _estado(pagina)
        r.cierto(e["indet"], "sin total, la barra corre sola")
        r.igual(e["der"], "", "y no inventa un porcentaje")
        r.cierto("9.0 MB" in e["izq"], "pero sí dice cuánto lleva")

        # Comprobando y listo.
        pagina.evaluate(f"{B}.mostrar({{titulo: 'Comprobando…', pct: 100, ya: 124000000, total: 124000000}})")
        r.igual(_estado(pagina)["ancho"], "100%", "al comprobar, la barra está llena")
        pagina.evaluate(f"{B}.mostrar({{titulo: 'draw101 9.9.9 bajado y comprobado.', pct: 100, estado: 'listo'}})")
        e = _estado(pagina)
        r.cierto(e["fin"] and not e["mal"], "al terminar bien se marca como terminada")
        pagina.evaluate(f"{B}.cerrar()")
        r.cierto(not _estado(pagina)["visible"], "y se cierra")

        # Fallo.
        pagina.evaluate(f"{B}.mostrar({{titulo: 'No se pudo bajar', pct: 100, estado: 'error'}})")
        e = _estado(pagina)
        r.cierto(e["visible"] and e["mal"], "un fallo se marca en rojo")
        r.cierto(not e["fin"], "y no se marca como terminada")
        pagina.evaluate(f"{B}.cerrar()")

        # No tapa la consola ni la línea de comandos.
        pagina.evaluate(f"{B}.mostrar({{titulo: 'Bajando…', pct: 10, ya: 1, total: 10}})")
        tapa = pagina.evaluate("""() => {
            const b = document.getElementById('barra-descarga').getBoundingClientRect();
            const c = document.getElementById('cmd').getBoundingClientRect();
            return !(b.bottom < c.top || b.top > c.bottom);
        }""")
        r.cierto(not tapa, "no tapa la línea de comandos")
        pagina.evaluate(f"{B}.cerrar()")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
