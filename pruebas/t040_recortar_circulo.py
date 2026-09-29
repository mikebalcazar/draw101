"""t040 · RECORTAR sobre círculos.

Mike (28-sep-2026): «cuando trazo un círculo, no puedo trimearlo con otras
líneas. TODAS las líneas se deberían poder trimear sea círculo, recta,
polilinea, arco, etc.». RECORTAR rechazaba el círculo con un aviso.

Lo que se mide aquí:

  · un círculo recortado se vuelve ARCO, y el arco que queda es el que NO
    tiene el clic dentro;
  · se recorta por el lado que se pica, no siempre por el mismo;
  · con cuatro cruces se quita sólo el cuadrante que se señaló, no medio
    círculo;
  · el arco hereda capa y color del círculo, y NO se queda con el handle del
    DXF (ya no es la entidad que venía en el archivo);
  · con un solo cruce (una tangente) no se recorta y se dice por qué: un
    círculo no tiene extremos, hacen falta dos cruces para abrirlo.

Se dibuja con comandos, se pica con el ratón sobre el trozo a quitar, y se
comprueba contra el motor.
"""

from __future__ import annotations

import json
import urllib.request

from pruebas import comun, navegador

DESCRIPCION = "RECORTAR corta círculos (quedan arco) y quita el trozo de en medio de un arco"


def _entidad(base: str, id_: str) -> dict:
    with urllib.request.urlopen(base + f"/api/entidad/{id_}", timeout=5) as f:
        return json.loads(f.read().decode("utf-8"))


def _cmd(pagina, *textos):
    for t in textos:
        pagina.click("#cmd")
        pagina.keyboard.press("Control+A")
        pagina.keyboard.press("Backspace")
        pagina.type("#cmd", t, delay=10)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(250)


def _clic(pagina, p) -> None:
    x, y = pagina.evaluate("""(p) => {
        const [x, y] = aPX(p[0], p[1]);
        const caja = document.querySelector('#lienzo').getBoundingClientRect();
        return [caja.left + x, caja.top + y];
    }""", list(p))
    pagina.mouse.move(x, y)
    pagina.wait_for_timeout(80)
    pagina.mouse.click(x, y)
    pagina.wait_for_timeout(400)


def _ids(base) -> list[str]:
    return sorted({t["id"] for t in navegador.trazos(base)}, key=lambda s: int(s[1:]))


def _de_tipo(base, tipo) -> list[dict]:
    return [e for e in (_entidad(base, i) for i in _ids(base)) if e.get("tipo") == tipo]


def _limpiar(pagina, base) -> None:
    ids = _ids(base)
    if ids:
        pagina.evaluate("(ids) => post('/api/operacion', {accion: 'limpiar', borrar: ids})", ids)
        pagina.evaluate("async () => { await recargarTrazos(); Seleccion.limpiar(); }")
        pagina.wait_for_timeout(300)


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""() => {
            estado.prefs.osnap = false; estado.prefs.ortho = false;
            estado.prefs.snap_rejilla = false; estado.prefs.dinamica = false;
            encuadrarCaja(-900, -900, 900, 900);
        }""")
        pagina.wait_for_timeout(200)
        _pica_la_derecha(r, pagina, base)
        _limpiar(pagina, base)
        _pica_la_izquierda(r, pagina, base)
        _limpiar(pagina, base)
        _cuatro_cruces(r, pagina, base)
        _limpiar(pagina, base)
        _una_tangente_no_alcanza(r, pagina, base)
        _limpiar(pagina, base)
        _el_arco_por_en_medio(r, pagina, base)
        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")


def _corta(pagina, donde) -> None:
    _cmd(pagina, "RECORTAR")
    _clic(pagina, donde)
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(300)


def _pica_la_derecha(r: comun.Reporte, pagina, base) -> None:
    """Círculo r=500 en el origen y una vertical en x=300, que lo cruza en
    (300, ±400) — o sea en 53.13° y en 306.87°. Se pica la tapa derecha, en
    (500,0): se va esa tapa y queda el trozo grande, de 53.13° a 306.87°."""
    _cmd(pagina, "CIRCULO", "0,0", "500")
    pagina.keyboard.press("Escape")
    _cmd(pagina, "LINEA", "300,-800", "300,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)
    r.igual(len(_de_tipo(base, "circulo")), 1, "hay un círculo antes de recortar")

    _corta(pagina, [500, 0])

    r.igual(len(_de_tipo(base, "circulo")), 0, "el círculo recortado ya no es círculo")
    arcos = _de_tipo(base, "arco")
    if r.igual(len(arcos), 1, "quedó UN arco en su lugar"):
        a = arcos[0]
        r.punto(a["centro"][:2], [0, 0], "con el mismo centro")
        r.casi(a["radio"], 500, "y el mismo radio")
        r.casi(a["ang_ini"] % 360, 53.13010235, "arranca en el cruce de arriba", tol=1e-4)
        r.casi(a["ang_fin"] % 360, 306.8698976, "y termina en el de abajo: se quedó el trozo grande, no la tapa", tol=1e-4)
        r.cierto(not a.get("handle_origen"), "y no hereda el handle del DXF: ya no es la entidad del archivo")


def _pica_la_izquierda(r: comun.Reporte, pagina, base) -> None:
    """El mismo dibujo, pero picando en (-500,0). Ahora lo que se va es el
    trozo grande y queda la tapa derecha: de 306.87° a 53.13°."""
    _cmd(pagina, "CIRCULO", "0,0", "500")
    pagina.keyboard.press("Escape")
    _cmd(pagina, "LINEA", "300,-800", "300,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    _corta(pagina, [-500, 0])

    arcos = _de_tipo(base, "arco")
    if r.igual(len(arcos), 1, "picando del otro lado también recorta"):
        a = arcos[0]
        r.casi(a["ang_ini"] % 360, 306.8698976, "y ahora lo que queda es la TAPA: arranca abajo", tol=1e-4)
        r.casi(a["ang_fin"] % 360, 53.13010235, "y termina arriba, pasando por el 0", tol=1e-4)


def _cuatro_cruces(r: comun.Reporte, pagina, base) -> None:
    """Círculo r=500 en una capa propia y de color propio, cruzado por dos
    líneas: x=0 y y=0, que lo parten en los cuatro cuadrantes. Se pica el
    primer cuadrante, en (350,350): se va SÓLO ese cuadrante y queda un arco
    de tres cuartos, de 90° a 0°."""
    pagina.evaluate("""async () => {
        await post('/api/capa', {nombre: 'CORTES', color: '#FF00FF', grosor: 35, tipo_linea: 'CONTINUOUS'});
    }""")
    pagina.wait_for_timeout(200)
    pagina.evaluate("""async () => {
        await post('/api/operacion', {accion: 'poner', agregar: [
            {tipo: 'circulo', centro: [0, 0], radio: 500, capa: 'CORTES', color: '#123456'}]});
        await recargarTrazos();
    }""")
    pagina.wait_for_timeout(300)
    _cmd(pagina, "LINEA", "0,-800", "0,800")
    pagina.keyboard.press("Escape")
    _cmd(pagina, "LINEA", "-800,0", "800,0")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    _corta(pagina, [353, 353])

    arcos = _de_tipo(base, "arco")
    if r.igual(len(arcos), 1, "con cuatro cruces sigue quedando un solo arco"):
        a = arcos[0]
        r.casi(a["ang_ini"] % 360, 90, "arranca en el cruce de arriba", tol=1e-4)
        r.casi(a["ang_fin"] % 360, 0, "y termina en el de la derecha: se quitó SÓLO el cuadrante, no la mitad", tol=1e-4)
        r.igual(a.get("capa"), "CORTES", "el arco se queda en la capa del círculo")
        r.igual(a.get("color"), "#123456", "y con su color, no con el de la capa activa")


def _una_tangente_no_alcanza(r: comun.Reporte, pagina, base) -> None:
    """Círculo r=500 en el origen y una horizontal en y=500, que lo toca en un
    solo punto. No hay por dónde abrirlo: se avisa y el círculo sigue ahí."""
    _cmd(pagina, "CIRCULO", "0,0", "500")
    pagina.keyboard.press("Escape")
    _cmd(pagina, "LINEA", "-800,500", "800,500")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    _corta(pagina, [500, 0])

    r.igual(len(_de_tipo(base, "circulo")), 1, "con un solo cruce el círculo se queda entero")
    r.igual(len(_de_tipo(base, "arco")), 0, "y no aparece ningún arco a medias")
    dicho = pagina.evaluate("""() => {
        const c = document.querySelector('#cmd-historial');
        return [...c.querySelectorAll('.eco')].slice(-4).map((e) => e.textContent).join(' | ');
    }""")
    r.cierto("dos cruces" in dicho, "y se dice por qué, no se queda callado", dicho)


def _el_arco_por_en_medio(r: comun.Reporte, pagina, base) -> None:
    """Un arco de 0° a 180°, radio 500, cruzado por dos verticales en x=−250 y
    x=250 —o sea en 120° y en 60°—. Se pica ARRIBA, en (0,500), que es el trozo
    de en medio: tiene que irse sólo ese trozo y quedar DOS arcos, uno a cada
    lado. Hasta el 28-sep-2026 se borraba todo lo que seguía al clic, que es el
    mismo hueco que Mike describió para el círculo.
    """
    pagina.evaluate("""async () => {
        await post('/api/operacion', {accion: 'poner', agregar: [
            {tipo: 'arco', centro: [0, 0], radio: 500, ang_ini: 0, ang_fin: 180}]});
        await recargarTrazos();
    }""")
    pagina.wait_for_timeout(300)
    _cmd(pagina, "LINEA", "250,-100", "250,800")
    pagina.keyboard.press("Escape")
    _cmd(pagina, "LINEA", "-250,-100", "-250,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)
    r.igual(len(_de_tipo(base, "arco")), 1, "hay un arco antes de recortar")

    _corta(pagina, [0, 500])

    arcos = _de_tipo(base, "arco")
    if r.igual(len(arcos), 2, "en medio: el arco queda en DOS arcos, no se borra lo que sigue"):
        arcos.sort(key=lambda e: e["ang_ini"] % 360)
        a, b = arcos
        r.casi(a["ang_ini"] % 360, 0, "el primero arranca donde arrancaba", tol=1e-4)
        r.casi(a["ang_fin"] % 360, 60, "y termina en el cruce de la derecha", tol=1e-4)
        r.casi(b["ang_ini"] % 360, 120, "el segundo arranca en el cruce de la izquierda", tol=1e-4)
        r.casi(b["ang_fin"] % 360, 180, "y termina donde terminaba", tol=1e-4)
