"""t028 · Las pestañas de dibujos se ven siempre.

Mike (16-sep-2026): «siempre mantén las pestañas de archivo abierto, aunque sea
uno solo; que no sólo se hagan pestañas cuando hay 2 o más».

Antes la fila se escondía con menos de dos dibujos. Con uno no se veía cómo se
llama, si tiene cambios sin guardar, ni el botón «+» para abrir otro; y al
abrir el segundo la fila aparecía de golpe y el lienzo daba un brinco.

Se comprueba en el navegador: con un dibujo recién arrancado, con dos, y al
cerrar uno de los dos (que es donde antes desaparecía).
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "la fila de pestañas se ve con uno, con dos y al cerrar"


def _fila(pagina):
    return pagina.evaluate("""() => {
        const b = document.getElementById('docs');
        const r = b.getBoundingClientRect();
        return {oculta: b.hidden, alto: r.height,
                pestanas: b.querySelectorAll('.pest').length,
                mas: !!document.getElementById('doc-mas'),
                nombres: [...b.querySelectorAll('.pest .n')].map((n) => n.textContent)};
    }""")


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.wait_for_timeout(300)

        f = _fila(pagina)
        r.cierto(not f["oculta"], "con un solo dibujo, la fila se ve")
        r.cierto(f["alto"] > 0, f"y ocupa su alto ({f['alto']:.0f} px)")
        r.igual(f["pestanas"], 1, "con su única pestaña")
        r.cierto(f["mas"], "y el botón «+» para abrir otro")
        r.cierto(f["nombres"] and f["nombres"][0], f"que dice cómo se llama ({f['nombres']})")

        alto1 = f["alto"]
        pagina.evaluate("Marco.nuevoDoc()")
        pagina.wait_for_timeout(500)
        f = _fila(pagina)
        r.igual(f["pestanas"], 2, "al abrir el segundo hay dos pestañas")
        r.cierto(not f["oculta"] and abs(f["alto"] - alto1) < 1,
                 "y la fila no cambia de alto: el lienzo no brinca")

        # Cerrar uno: antes aquí desaparecía la fila.
        pagina.evaluate("Marco.cerrarDoc(estado.escritorio.documentos[1].indice)")
        pagina.wait_for_timeout(500)
        f = _fila(pagina)
        r.igual(f["pestanas"], 1, "al cerrar el segundo queda una pestaña")
        r.cierto(not f["oculta"], "y la fila sigue ahí")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
