"""t025 · El sugeridor de comandos.

Mike (16-sep-2026): «si tecleas C, que sugiera COPY o CIRCLE o lo que empiece
con C». Las reglas vienen del chat de shape101, que lo hizo primero:

  1. Primero va lo que Enter correría ahora mismo (con «C», CIRCULO, porque
     ése es su atajo), luego del nombre más corto al más largo.
  2. Las flechas: con la caja vacía, historial; con algo tecleado y
     sugerencias, eligen entre ellas.
  3. Al elegir, el nombre se escribe en la caja: Enter corre lo escrito.
  4. Se busca por nombre y por atajo, en español y en inglés.
  5. Ocho como mucho, arriba de la caja, y **compacta**: Mike (16-sep, con
     captura) la vio demasiado grande, así que se mide el ancho, el alto de
     fila y que la ayuda venga recortada.

Se prueba en el navegador con los comandos de verdad del programa.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "el sugeridor: orden, los dos idiomas, flechas e historial"


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        _orden(r, pagina)
        _pantalla(r, pagina)
        _flechas(r, pagina)
        r.igual(pagina.errores, [], "sin errores de JavaScript")


def _nombres(pagina, texto):
    return pagina.evaluate("(t) => Sugeridor.buscar(t).map((o) => o.cmd.nombre)", texto)


def _orden(r: comun.Reporte, pagina) -> None:
    c = _nombres(pagina, "C")
    if r.cierto(c, "«C» da sugerencias"):
        r.igual(c[0], "CIRCULO", "y encabeza CIRCULO: es lo que Enter correría con «C»")
        r.cierto(len(c) <= 8, f"ocho como mucho (salieron {len(c)})")
        r.cierto("COTA" in c and "COPIAR" in c, "con COTA y COPIAR en la lista")

    co = _nombres(pagina, "CO")
    r.igual(co[0], "COPIAR", "«CO» encabeza COPIAR: es su atajo")
    cot = _nombres(pagina, "COT")
    r.igual(cot[0], "COTA", "«COT» encabeza COTA (las COTAH, COTAV… siguen detrás)")
    r.igual(_nombres(pagina, "RECTANG")[0], "RECTANGULO", "«RECTANG» lleva a RECTANGULO")
    r.igual(_nombres(pagina, "ZZQQ"), [], "lo que no existe no sugiere nada")
    r.igual(_nombres(pagina, ""), [], "la caja vacía tampoco")
    r.igual(_nombres(pagina, "100,50"), [], "una coordenada no sugiere comandos")
    r.igual(_nombres(pagina, "-200"), [], "ni un número")

    # Los dos idiomas: quien teclea CIRCLE encuentra CIRCULO.
    r.igual(_nombres(pagina, "CIRCLE"), ["CIRCULO"], "«CIRCLE» encuentra CIRCULO (inglés)")
    r.cierto("MOVER" in _nombres(pagina, "MOVE"), "«MOVE» encuentra MOVER")
    r.cierto("ESCALAR" in _nombres(pagina, "SCALE"), "«SCALE» encuentra ESCALAR")


def _pantalla(r: comun.Reporte, pagina) -> None:
    m = pagina.evaluate("""() => {
        const c = document.getElementById('cmd');
        c.focus(); c.value = 'C'; c.dispatchEvent(new Event('input'));
        const l = document.getElementById('sugerencias');
        const caja = c.getBoundingClientRect(), r = l.getBoundingClientRect();
        return {visible: getComputedStyle(l).display !== 'none', filas: l.children.length,
                arriba: r.bottom <= caja.top + 1, dentro: r.top >= 0,
                ancho: r.width, altoFila: l.children[0].getBoundingClientRect().height,
                ayuda: l.children[0].querySelector('span').textContent,
                primera: l.children[0] && l.children[0].querySelector('b').textContent};
    }""")
    r.cierto(m["visible"], "la lista se ve al teclear")
    r.cierto(m["filas"] >= 3, f"con varias filas ({m['filas']})")
    r.cierto(m["arriba"] and m["dentro"], "arriba de la consola y dentro de la ventana")
    r.cierto(m["ancho"] <= 420, f"y compacta: no más de 420 px de ancho ({m['ancho']:.0f})")
    r.cierto(m["altoFila"] <= 22, f"con renglones bajitos ({m['altoFila']:.0f} px)")
    # En inglés la fila enseña el nombre en inglés (el programa arranca en en).
    r.cierto(m["primera"] in ("CIRCULO", "CIRCLE"), f"y la primera fila es el círculo ({m['primera']})")
    r.cierto(len(m["ayuda"]) <= 47, f"la ayuda va recortada a una idea ({len(m['ayuda'])} letras: «{m['ayuda']}»)")


def _flechas(r: comun.Reporte, pagina) -> None:
    # Con algo tecleado, la flecha elige entre sugerencias y escribe el nombre.
    v = pagina.evaluate("""() => {
        const c = document.getElementById('cmd');
        c.focus(); c.value = 'C'; c.dispatchEvent(new Event('input'));
        return c.value;
    }""")
    r.igual(v, "C", "lo tecleado no se completa solo")
    pagina.keyboard.press("ArrowDown")
    r.igual(pagina.evaluate("document.getElementById('cmd').value"), "CIRCULO",
            "la flecha abajo escribe CIRCULO en la caja (no borra lo tecleado)")
    pagina.keyboard.press("ArrowDown")
    r.igual(pagina.evaluate("document.getElementById('cmd').value"), "COTA",
            "y la siguiente baja a COTA")
    pagina.keyboard.press("Escape")
    pagina.evaluate("() => { const c = document.getElementById('cmd'); c.value = ''; c.dispatchEvent(new Event('input')); }")

    # Con la caja vacía, las flechas siguen siendo el historial.
    navegador.comando(pagina, "ENCUADRAR")
    pagina.wait_for_timeout(200)
    pagina.evaluate("document.getElementById('cmd').focus()")
    pagina.keyboard.press("ArrowUp")
    r.igual(pagina.evaluate("document.getElementById('cmd').value"), "ENCUADRAR",
            "con la caja vacía, la flecha arriba trae el historial")
    pagina.evaluate("() => { const c = document.getElementById('cmd'); c.value = ''; c.dispatchEvent(new Event('input')); c.blur(); }")
