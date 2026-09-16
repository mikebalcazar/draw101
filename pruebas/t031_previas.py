"""t031 · Previas: que se vea cómo va quedando antes de soltar el clic.

Mike (16-sep-2026): «en TODAS las herramientas necesito que se vaya dibujando
el preview de cómo queda la operación. Así como en MOVER se ve dónde estás
arrastrando la entidad, en la elipse se debería ver cómo se va dibujando
mientras vas colocando los puntos; cuando mueves un endpoint de una línea o
entidad, que se vea cómo se va dibujando según la vas moviendo».

La mayoría ya tenía previa. Esta prueba cubre las que no, y la que peor se
veía:

  · **grips** — antes sólo una raya del grip al cursor; ahora se pinta la
    entidad entera con ese vértice ya movido.
  · **DESFASE** — la copia donde va a quedar, calculada con la misma función
    que la hace de verdad.
  · **PUNTO** y **TEXTO** — la marca y la caja del texto a su altura.
  · y el fantasma sabe pintar círculos y arcos como curvas, no como polígonos.
"""

from __future__ import annotations

import math

from pruebas import comun, navegador

DESCRIPCION = "previas: grips, desfase, punto y texto"


def _mover(pagina, p):
    x, y = pagina.evaluate("""(p) => {
        const [x, y] = aPX(p[0], p[1]);
        const caja = document.querySelector('#lienzo').getBoundingClientRect();
        return [caja.left + x, caja.top + y];
    }""", list(p))
    pagina.mouse.move(x, y)
    pagina.wait_for_timeout(120)
    return x, y


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""() => {
            estado.prefs.osnap = false; estado.prefs.ortho = false;
            estado.prefs.snap_rejilla = false; estado.prefs.dinamica = false;
            encuadrarCaja(-200, -200, 1600, 1200);
        }""")
        pagina.wait_for_timeout(200)
        _grip(r, pagina)
        _desfase(r, pagina)
        _punto_y_texto(r, pagina)
        _curvas(r, pagina)
        r.igual(pagina.errores, [], "sin errores de JavaScript")


def _grip(r: comun.Reporte, pagina) -> None:
    """Una polilínea de cuatro vértices: al jalar uno se ve la polilínea
    entera con ese vértice movido, no sólo una raya."""
    navegador.comando(pagina, "POLILINEA")
    for p in ("0,0", "400,0", "400,300", "800,300"):
        navegador.comando(pagina, p)
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    ids = pagina.evaluate("estado.trazos.map((t) => t.id)")
    r.igual(len(ids), 1, "hay una polilínea")
    pagina.evaluate("(ids) => { estado.sel.clear(); ids.forEach((i) => estado.sel.add(i)); }", ids)

    # Se arrastra de verdad: del vértice (400,300) a (600,700).
    _mover(pagina, [400, 300])
    pagina.mouse.down()
    _mover(pagina, [600, 700])
    hule = pagina.evaluate("""() => {
        const h = estado.hule || {};
        const f = h.fantasma || [];
        return {hay: f.length > 0, puntos: f[0] ? f[0].puntos : null};
    }""")
    if r.cierto(hule["hay"], "al jalar el grip se pinta la entidad como fantasma"):
        pts = hule["puntos"]
        r.igual(len(pts), 4, "con sus cuatro vértices")
        r.punto(pts[0], [0, 0], "el primero no se mueve", 0.5)
        r.punto(pts[2], [600, 700], "el que se jala va al cursor", 2)   # el ratón apunta con la resolución del píxel
        r.punto(pts[3], [800, 300], "y el último se queda donde estaba", 0.5)
    pagina.mouse.up()
    pagina.wait_for_timeout(300)
    pagina.keyboard.press("Escape")


def _desfase(r: comun.Reporte, pagina) -> None:
    """Al elegir el lado del desfase se ve la copia donde va a quedar."""
    pagina.evaluate("estado.sel.clear()")
    navegador.comando(pagina, "LINEA")
    navegador.comando(pagina, "0,900")
    navegador.comando(pagina, "800,900")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    navegador.comando(pagina, "DESFASE")
    navegador.comando(pagina, "50")          # distancia
    pagina.mouse.click(*_mover(pagina, [400, 900]))     # picar la línea
    pagina.wait_for_timeout(300)
    _mover(pagina, [400, 1000])              # de este lado
    f = pagina.evaluate("((estado.hule || {}).fantasma || [])[0] || null")
    if r.cierto(f is not None, "el desfase enseña la copia antes del clic"):
        r.cierto(abs(f["puntos"][0][1] - 950) < 1, f"del lado del cursor (y={f['puntos'][0][1]:.0f}, esperado 950)")
        _mover(pagina, [400, 800])           # y del otro lado se pasa sola
        f2 = pagina.evaluate("((estado.hule || {}).fantasma || [])[0] || null")
        r.cierto(f2 and abs(f2["puntos"][0][1] - 850) < 1,
                 "y cambia de lado con el cursor, sin hacer clic")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)


def _punto_y_texto(r: comun.Reporte, pagina) -> None:
    navegador.comando(pagina, "PUNTO")
    _mover(pagina, [1200, 200])
    h = pagina.evaluate("estado.hule && (estado.hule.partes || [])[0] || null")
    r.cierto(h and h["tipo"] == "marca", "PUNTO enseña la marca donde va a caer")
    pagina.keyboard.press("Escape")

    navegador.comando(pagina, "TEXTO")
    _mover(pagina, [1200, 400])
    f = pagina.evaluate("((estado.hule || {}).fantasma || [])[0] || null")
    if r.cierto(f is not None, "TEXTO enseña una previa"):
        r.igual(f["clase"], "texto", "que es un texto")
        r.cierto(f["altura"] > 0, f"a la altura que se va a usar ({f['altura']})")
    pagina.keyboard.press("Escape")


def _curvas(r: comun.Reporte, pagina) -> None:
    """El fantasma pinta círculos y arcos como curvas: antes sólo sabía de
    líneas y un círculo desfasado salía poligonal."""
    ok = pagina.evaluate("""() => {
        const antes = estado.hule;
        estado.hule = {fantasma: [{clase: 'circulo', c: [600, 600], r: 100}]};
        let error = null;
        try { pintarYa(); } catch (e) { error = String(e); }
        estado.hule = antes; pintarYa();
        return error;
    }""")
    r.igual(ok, None, "el fantasma pinta un círculo sin reventar")
    ok = pagina.evaluate("""() => {
        const antes = estado.hule;
        estado.hule = {fantasma: [{clase: 'arco', c: [600, 600], r: 100, a0: 0, a1: 90}]};
        let error = null;
        try { pintarYa(); } catch (e) { error = String(e); }
        estado.hule = antes; pintarYa();
        return error;
    }""")
    r.igual(ok, None, "y un arco también")
