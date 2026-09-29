"""t041 · RECORTAR sobre elipses y splines.

Mike (28-sep-2026): «hagamos correcto el recorte de elipse y spline. Corrijamos
si necesita corregirse el trazo».

SÍ necesitaba corregirse. La spline se DIBUJABA como curva suave pero su
geometría —la que usa el osnap y la que busca los cruces— eran las rectas entre
sus puntos: el zigzag. En una spline de cuatro puntos el error medido fue de 15
unidades, o sea que los cruces caían donde la curva no está. Eso se arregló en
`core/geometria.py` antes de tocar el recorte, y aquí se mide.

Lo que se comprueba:

  ELIPSE — se recorta y SIGUE SIENDO ELIPSE (ya guarda su tramo en param_ini y
  param_fin, así que no hay que cambiarle el tipo). Y el corte es EXACTO: la
  punta del tramo que queda cae sobre la línea que cortó con error de millonésimas,
  no sobre la aproximación de 72 segmentos con la que se dibuja —que erraría
  medio milímetro por cada 500 de radio, y eso en un plano se ve.

  SPLINE — se recorta y SIGUE SIENDO SPLINE, que es lo que Mike escogió con
  botones. La curva sigue pasando por los puntos que él puso, el corte cae
  exacto sobre la línea, y lo que estaba del lado quitado ya no se dibuja.

  SPLINE CV (por puntos de control) — la forma no se puede conservar como curva
  de control porque los nudos no se guardan; queda como spline por puntos de
  paso recorriendo la MISMA curva, y se dice.
"""

from __future__ import annotations

import json
import math
import urllib.request

from pruebas import comun, navegador

DESCRIPCION = "RECORTAR corta elipses (exacto) y splines (y siguen siendo spline)"


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


def _puntos_dibujados(base, id_) -> list[list[float]]:
    """Los puntos de la polilínea con que el motor dibuja esa entidad."""
    salida = []
    for t in navegador.trazos(base):
        if t["id"] == id_:
            salida.extend(t.get("puntos") or [])
    return salida


def _poner(pagina, datos) -> None:
    pagina.evaluate("""async (d) => {
        await post('/api/operacion', {accion: 'poner', agregar: [d]});
        await recargarTrazos();
    }""", datos)
    pagina.wait_for_timeout(350)


def _limpiar(pagina, base) -> None:
    ids = _ids(base)
    if ids:
        pagina.evaluate("(ids) => post('/api/operacion', {accion: 'limpiar', borrar: ids})", ids)
        pagina.evaluate("async () => { await recargarTrazos(); Seleccion.limpiar(); }")
        pagina.wait_for_timeout(300)


def _corta(pagina, donde) -> None:
    _cmd(pagina, "RECORTAR")
    _clic(pagina, donde)
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(300)


def correr(r: comun.Reporte) -> None:
    _la_geometria_de_la_spline(r)
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: el resto se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""() => {
            estado.prefs.osnap = false; estado.prefs.ortho = false;
            estado.prefs.snap_rejilla = false; estado.prefs.dinamica = false;
            encuadrarCaja(-900, -900, 1200, 900);
        }""")
        pagina.wait_for_timeout(200)
        _elipse_cerrada(r, pagina, base)
        _limpiar(pagina, base)
        _elipse_girada(r, pagina, base)
        _limpiar(pagina, base)
        _spline_por_un_lado(r, pagina, base)
        _limpiar(pagina, base)
        _spline_en_medio(r, pagina, base)
        _limpiar(pagina, base)
        _spline_de_control(r, pagina, base)
        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")


def _la_geometria_de_la_spline(r: comun.Reporte) -> None:
    """Sin navegador: que la geometría de la spline sea la CURVA, no el zigzag.

    Es el arreglo de fondo. Mientras la geometría fueran las rectas entre los
    puntos, ni el osnap ni los cruces caían sobre la curva que se ve.
    """
    from core import dibujo, geometria
    from core import entidades as E

    class Doc:
        pass

    sp = E.Spline(puntos_ajuste=[[0, 0], [100, 200], [200, -200], [300, 0]])
    prim = geometria.primitivas_de(Doc(), sp)
    curva = dibujo._spline(sp.puntos_ajuste, False)
    r.cierto(len(prim) > 30, "la geometría de la spline tiene los segmentos de la curva, no tres rectas",
             f"{len(prim)} primitivas")
    peor = max(min(math.dist(q, c) for c in curva) for pr in prim for q in (pr["a"], pr["b"]))
    r.casi(peor, 0, "y cada uno cae EXACTAMENTE sobre la curva que se dibuja", tol=1e-9)

    sc = E.Spline(puntos_control=[[0, 0], [100, 200], [200, -200], [300, 0]], grado=3)
    pc = geometria.primitivas_de(Doc(), sc)
    cb = dibujo._bspline(sc.puntos_control, 3, False)
    peor2 = max(min(math.dist(q, c) for c in cb) for pr in pc for q in (pr["a"], pr["b"]))
    r.casi(peor2, 0, "y con puntos de control, sobre la curva de control", tol=1e-9)


def _elipse_cerrada(r: comun.Reporte, pagina, base) -> None:
    """Elipse a=500, b=250 en el origen, cortada por la vertical x=300. Se pica
    la tapa derecha: queda el trozo grande, SIGUE SIENDO ELIPSE, y la punta del
    trozo cae exactamente en x=300."""
    _poner(pagina, {"tipo": "elipse", "centro": [0, 0], "eje_mayor": [500, 0], "razon": 0.5})
    _cmd(pagina, "LINEA", "300,-800", "300,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)
    r.igual(len(_de_tipo(base, "elipse")), 1, "hay una elipse antes de recortar")

    _corta(pagina, [500, 0])

    els = _de_tipo(base, "elipse")
    if r.igual(len(els), 1, "la elipse recortada SIGUE siendo elipse, no se vuelve otra cosa"):
        e = els[0]
        esperado = math.acos(300 / 500)          # 0.9272952180016122 rad
        r.casi(e["param_ini"] % (2 * math.pi), esperado, "arranca en el cruce de arriba", tol=1e-6)
        r.casi(e["param_fin"] % (2 * math.pi), 2 * math.pi - esperado, "y termina en el de abajo", tol=1e-6)
        # LO QUE DE VERDAD IMPORTA: la punta cae sobre la línea que cortó.
        x = 500 * math.cos(e["param_ini"])
        r.casi(x, 300, "y la punta cae EXACTO sobre la línea que cortó, no a medio milímetro", tol=1e-6)
        pts = _puntos_dibujados(base, e["id"])
        r.cierto(pts and max(q[0] for q in pts) <= 300 + 1e-6,
                 "lo que quedó ya no se dibuja del lado que se quitó",
                 f"el punto más a la derecha está en x={max(q[0] for q in pts):.6f}")


def _elipse_girada(r: comun.Reporte, pagina, base) -> None:
    """La misma, girada 30°, cortada por una horizontal. Si el marco de la
    elipse estuviera mal armado, el giro lo destapa."""
    g = math.radians(30)
    _poner(pagina, {"tipo": "elipse", "centro": [0, 0],
                    "eje_mayor": [500 * math.cos(g), 500 * math.sin(g)], "razon": 0.5})
    _cmd(pagina, "LINEA", "-800,120", "800,120")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    # El clic tiene que caer SOBRE la elipse o no se selecciona nada. El punto
    # del parámetro 180° de la elipse girada: (-433, -250), muy por debajo de la
    # horizontal que corta.
    _corta(pagina, [-500 * math.cos(g), -500 * math.sin(g)])

    els = _de_tipo(base, "elipse")
    if r.igual(len(els), 1, "girada: también se recorta y sigue siendo elipse"):
        e = els[0]
        a = 500.0
        b = 250.0
        for cual in ("param_ini", "param_fin"):
            t = e[cual]
            x, y = a * math.cos(t), b * math.sin(t)
            py = x * math.sin(g) + y * math.cos(g)
            r.casi(py, 120, f"la punta {cual} cae exacto sobre la horizontal que cortó", tol=1e-6)


def _spline_por_un_lado(r: comun.Reporte, pagina, base) -> None:
    """Spline por cinco puntos de paso, cruzada una vez por la vertical x=250.
    Se pica antes del cruce: se va ese arranque, el resto sigue siendo spline y
    conserva los puntos de paso que quedaron dentro."""
    fit = [[0, 0], [150, 250], [350, -250], [550, 200], [750, 0]]
    _poner(pagina, {"tipo": "spline", "puntos_ajuste": fit, "grado": 3})
    _cmd(pagina, "LINEA", "250,-800", "250,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)
    antes = _de_tipo(base, "spline")
    r.igual(len(antes), 1, "hay una spline antes de recortar")
    dib = _puntos_dibujados(base, antes[0]["id"])
    r.cierto(min(q[0] for q in dib) < 250, "y arranca del lado izquierdo de la línea")

    _corta(pagina, [20, 20])

    sps = _de_tipo(base, "spline")
    if r.igual(len(sps), 1, "sigue habiendo UNA spline: no se volvió polilínea ni se partió"):
        e = sps[0]
        fitn = [[q[0], q[1]] for q in (e.get("puntos_ajuste") or [])]
        r.cierto(len(fitn) >= 3, "con tres puntos de paso o más: sigue siendo curva, no una recta",
                 f"{len(fitn)} puntos")
        r.casi(fitn[0][0], 250, "arranca EXACTO sobre la línea que cortó", tol=1e-6)
        r.punto(fitn[-1], [750, 0], "y termina donde terminaba")
        quedaron = [q for q in fit if any(abs(q[0] - w[0]) < 1e-6 and abs(q[1] - w[1]) < 1e-6 for w in fitn)]
        r.cierto([350, -250] in quedaron and [550, 200] in quedaron,
                 "y conserva los puntos de paso que Mike puso del lado que se queda")
        dib2 = _puntos_dibujados(base, e["id"])
        r.cierto(dib2 and min(q[0] for q in dib2) >= 250 - 1e-6,
                 "y ya no se dibuja nada del lado que se quitó",
                 f"el punto más a la izquierda está en x={min(q[0] for q in dib2):.6f}")


def _spline_en_medio(r: comun.Reporte, pagina, base) -> None:
    """La misma spline, con DOS verticales. Se pica entre ellas: queda en dos
    splines, una a cada lado."""
    fit = [[0, 0], [150, 250], [350, -250], [550, 200], [750, 0]]
    _poner(pagina, {"tipo": "spline", "puntos_ajuste": fit, "grado": 3})
    _cmd(pagina, "LINEA", "150,-800", "150,800")
    pagina.keyboard.press("Escape")
    _cmd(pagina, "LINEA", "600,-800", "600,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    _corta(pagina, [350, -250])

    sps = _de_tipo(base, "spline")
    if r.igual(len(sps), 2, "en medio: la spline queda en DOS splines"):
        sps.sort(key=lambda e: (e.get("puntos_ajuste") or [[0]])[0][0])
        a, b = sps
        ax = [q[0] for q in _puntos_dibujados(base, a["id"])]
        bx = [q[0] for q in _puntos_dibujados(base, b["id"])]
        r.cierto(max(ax) <= 150 + 1e-6, "la primera no pasa de la primera línea", f"llega a x={max(ax):.6f}")
        r.cierto(min(bx) >= 600 - 1e-6, "y la segunda arranca en la segunda", f"empieza en x={min(bx):.6f}")


def _spline_de_control(r: comun.Reporte, pagina, base) -> None:
    """Spline por puntos de CONTROL. No se puede partir exacto como curva de
    control (los nudos no se guardan), así que queda por puntos de paso
    recorriendo la misma curva — y se avisa."""
    ctrl = [[0, 0], [100, 300], [300, -200], [500, 250], [700, -50], [900, 120]]
    _poner(pagina, {"tipo": "spline", "puntos_control": ctrl, "grado": 3})
    pagina.wait_for_timeout(200)
    antes = _de_tipo(base, "spline")[0]
    curva_antes = _puntos_dibujados(base, antes["id"])
    _cmd(pagina, "LINEA", "600,-800", "600,800")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(200)

    _corta(pagina, [850, 60])

    sps = _de_tipo(base, "spline")
    if r.igual(len(sps), 1, "la spline de control también se recorta"):
        e = sps[0]
        r.cierto(bool(e.get("puntos_ajuste")) and not e.get("puntos_control"),
                 "y queda como spline por puntos de paso, que es lo único que conserva la forma")
        dib = _puntos_dibujados(base, e["id"])
        r.cierto(dib and max(q[0] for q in dib) <= 600 + 1e-6,
                 "sin nada del lado que se quitó", f"llega a x={max(q[0] for q in dib):.6f}")
        # la forma que queda tiene que ser la MISMA curva de antes
        izq = [q for q in curva_antes if q[0] <= 600]
        peor = max(min(math.dist(q, w) for w in dib) for q in izq)
        r.cierto(peor < 1.0, "y recorre la misma curva que antes, no una parecida",
                 f"desviación máxima {peor:.4f} unidades")
        dicho = pagina.evaluate("""() => {
            const c = document.querySelector('#cmd-historial');
            return [...c.querySelectorAll('.eco')].slice(-4).map((e) => e.textContent).join(' | ');
        }""")
        r.cierto("puntos de control" in dicho, "y se avisa del cambio, no se hace a escondidas", dicho)
