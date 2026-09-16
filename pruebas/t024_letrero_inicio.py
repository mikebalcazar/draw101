"""t024 · El aviso de versión nueva se ve al arrancar, encima de la pantalla de inicio.

Mike (15-sep-2026, tres versiones seguidas): «sigue sin avisarme que hay una
actualización cuando arranco; sólo cuando voy a check for updates». La revisión
silenciosa sí corría y sí ponía el letrero, pero dentro del lienzo (z 7),
tapado por la pantalla de inicio (z 50, fija), que es donde uno está al
arrancar. Ahora el letrero va fijo en el body, por encima del inicio y por
debajo de los cuadros de diálogo.

Se abre el inicio, se le da al motor un puntero con versión 9.9.9 (como haría
el respaldo por Chromium) y se corre la revisión silenciosa: el letrero debe
existir y, sobre todo, ser lo que hay bajo el cursor en su centro.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "el letrero de versión nueva se ve encima de la pantalla de inicio"


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        pagina.evaluate("Marco.abrirInicio()")
        pagina.wait_for_timeout(200)
        r.cierto(pagina.evaluate("Marco.inicioAbierto()"), "la pantalla de inicio está abierta")
        m = pagina.evaluate("""async () => {
            await post('/api/actualizacion/manifiesto', {draw101: {version: '9.9.9', fecha: '2026-09-15', notas: ['prueba'],
                windows: {archivo: 'draw101-9.9.9-setup.exe', bytes: 5, sha256: 'x', url: 'https://ejemplo.invalido/x.exe'}}});
            const r = await Actualizar.revisar({silencio: true});
            const el = document.getElementById('letrero-version');
            if (!el) return {hay: r && r.hay_nueva, letrero: false};
            const c = el.getBoundingClientRect();
            const bajo = document.elementFromPoint(c.left + c.width / 2, c.top + c.height / 2);
            return {hay: r && r.hay_nueva, letrero: true, visible: !!bajo && el.contains(bajo),
                    inicioAbierto: Marco.inicioAbierto(), texto: el.textContent,
                    z: getComputedStyle(el).zIndex, pos: getComputedStyle(el).position, padre: el.parentElement.tagName};
        }""")
        r.cierto(m["hay"], "la revisión silenciosa ve la 9.9.9")
        if r.cierto(m["letrero"], "y pone el letrero"):
            r.cierto(m["inicioAbierto"], "con la pantalla de inicio todavía abierta")
            r.cierto(m["visible"], "el letrero es lo que hay bajo el cursor en su centro: no lo tapa el inicio")
            r.igual(m["padre"], "BODY", "cuelga del body, no del lienzo")
            r.igual(m["pos"], "fixed", "y va fijo")
            r.cierto("9.9.9" in m["texto"], "con la versión nueva en el texto")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
