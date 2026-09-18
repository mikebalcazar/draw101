"""t034 · La actualización se baja sola y, al terminar, pregunta si instalar.

Mike (18-sep-2026): «una vez que se descarga la actualización en draw101, ahí
mismo debería aparecer una ventana que pregunta si quieres instalar de una vez.
No hasta que te metas y lo hagas manual».

Antes: la revisión al arrancar ponía un letrero y ahí se quedaba; había que
picarlo, aceptar un cuadro, esperar la descarga, y sólo entonces salía la
pregunta. Ahora la revisión silenciosa baja el instalador sola (con su barra) y
al terminar abre el cuadro «Instalar draw101 X / Instalar ahora / Después». Y si
el instalador ya estaba bajado de una vez anterior, pregunta directo.

Se simula el motor: el puntero dice 9.9.9 y «bajar» contesta que ya quedó
listo, sin red de por medio.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "versión nueva: se baja sola y al terminar pregunta si instalar"


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: la prueba se salta)")
        return
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        m = pagina.evaluate("""async () => {
            // El puntero: hay una 9.9.9.
            await post('/api/actualizacion/manifiesto', {draw101: {version: '9.9.9', fecha: '2026-09-18', notas: ['prueba'],
                windows: {archivo: 'draw101-9.9.9-setup.exe', bytes: 5, sha256: 'x', url: 'https://ejemplo.invalido/x.exe'}}});
            // Aquí se corre en Linux, donde no se puede instalar un .exe. Se
            // envuelve fetch para contestar como en Windows (se_puede_instalar)
            // y para que «bajar» diga que ya quedó listo, sin tocar la red.
            const fetchReal = window.fetch;
            let pidioBajar = false;
            const json = (obj) => new Response(JSON.stringify(obj), {status: 200, headers: {'Content-Type': 'application/json'}});
            window.fetch = async (ruta, op) => {
                const u = String(ruta);
                if (u === '/api/actualizacion/bajar') {
                    pidioBajar = true;
                    return json({fase: 'listo', pct: 100, version: '9.9.9', ruta: 'C:\\\\tmp\\\\draw101-9.9.9-setup.exe', mensaje: 'listo'});
                }
                const resp = await fetchReal(ruta, op);
                if (u.startsWith('/api/actualizacion?')) {
                    const r = await resp.json(); r.se_puede_instalar = true; return json(r);
                }
                return resp;
            };
            // La revisión de arranque, silenciosa: la que antes sólo ponía el letrero.
            const antes = !!document.querySelector('.dlg');
            await Actualizar.revisar({silencio: true});
            await new Promise((ok) => setTimeout(ok, 400));
            const dlg = document.querySelector('.dlg');
            const titulo = dlg ? (dlg.querySelector('h2, h3, .titulo, header') || dlg).textContent : '';
            const botones = dlg ? [...dlg.querySelectorAll('button')].map((b) => b.textContent.trim()) : [];
            const letrero = !!document.getElementById('letrero-version');
            window.fetch = fetchReal;
            return {antes, pidioBajar, hayCuadro: !!dlg, titulo, botones, letrero};
        }""")
        r.cierto(not m["antes"], "sin nada abierto antes")
        r.cierto(m["pidioBajar"], "la revisión de arranque pide bajar la versión nueva sola")
        r.cierto(m["hayCuadro"], "y al terminar la descarga aparece un cuadro sin que nadie lo pida")
        r.cierto("9.9.9" in m["titulo"], f"que dice qué versión va a instalar ({m['titulo'][:40]})")
        # El programa de pruebas arranca en inglés: los botones salen traducidos.
        r.cierto(any(b in ("Instalar ahora", "Install now") for b in m["botones"]), f"con el botón de instalar ({m['botones']})")
        r.cierto(any(b in ("Después", "Later") for b in m["botones"]), "y el de «Después», para quien esté a media chamba")
        r.cierto(not m["letrero"], "y el letrero de «hay versión nueva» ya no estorba: la pregunta lo reemplaza")
        pagina.keyboard.press("Escape")
        r.igual(pagina.errores, [], "sin errores de JavaScript")
