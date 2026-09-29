"""t044 · Una ventana de la hoja puede ir SIN ESCALA, y ahí sí se hace zoom.

Mike, 29-sep-2026: «en el layout de plano, aparte de las escalas disponibles,
necesito una opción que diga sin escala donde pueda acercar o alejar el zoom
del viewport según requiera».

Es el S/E de un plano de verdad: un detalle o una vista que no se mide con
escalímetro y que uno encuadra como le acomode.

DOS COSAS QUE NO SE CRUZAN, y las dos se miden aquí:

  · una ventana SIN escala se acerca y se aleja con la rueda;
  · una ventana CON escala sigue intocable. Eso no es un olvido: es lo que
    Mike pidió el 9-sep —«no lo puedo editar ni hacer zoom: eso se hace con la
    escala»— y es lo que hace que el plano se pueda medir. Una ventana que
    dice 1:20 y no lo está es peor que una que no dice nada.

La rueda sólo manda con EDITARVENTANA encendido, que fue lo que Mike escogió
con botones: encima de la hoja la rueda significa «acercar la hoja», y que a
veces significara otra cosa según dónde esté el cursor sería una trampa.
"""

from __future__ import annotations

from pruebas import comun, navegador


DESCRIPCION = "una ventana de la hoja puede ir sin escala, y ahí la rueda sí acerca"


def correr(r: comun.Reporte) -> None:
    _el_rotulo(r)
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: lo de la rueda se salta)")
        return
    _la_rueda(r)


def _el_rotulo(r: comun.Reporte) -> None:
    """Lo que el pie de plano escribe en ESCALA. Es la mitad que se imprime."""
    from core import papel

    v = papel.ventana_nueva(0, 0, 100, 100, [0, 0], 20)
    r.cierto(v.get("sin_escala") is False, "una ventana nace CON escala, como siempre")
    r.igual(papel._escala_principal({"ventanas": [dict(v)]}), "1:20",
            "y el rótulo escribe su escala")

    se = dict(v, sin_escala=True)
    r.igual(papel._escala_principal({"ventanas": [se]}), "S/E",
            "marcada sin escala, el rótulo escribe S/E y no un número que sería mentira")
    r.igual(papel._escala_principal({"ventanas": [dict(se), dict(se, escala=7.3)]}), "S/E",
            "dos sin escala siguen siendo S/E, aunque por dentro tengan números distintos")
    r.igual(papel._escala_principal({"ventanas": [dict(v), se]}), "VARIAS",
            "mezcladas dice VARIAS: el número de abajo no valdría para todo el plano")

    # La escala SIGUE existiendo por dentro: es lo que convierte el modelo a
    # milímetros de papel. Si se perdiera, no habría nada que dibujar.
    r.cierto(se.get("escala", 0) > 0,
             "sin escala NO quiere decir sin número: por dentro sigue habiendo uno",
             str(se.get("escala")))


def _la_rueda(r: comun.Reporte) -> None:
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""async () => {
            await post('/api/operacion', {accion: 'poner', agregar: [
                {tipo: 'linea', p1: [0, 0], p2: [2000, 0]},
                {tipo: 'linea', p1: [0, 1000], p2: [2000, 1000]}]});
            await recargarTrazos();
            await post('/api/layout', {nombre: 'PLANO', ancho: 420, alto: 297});
            await Papel.entrar(0);
        }""")
        pagina.wait_for_timeout(700)

        def esc():
            return pagina.evaluate("() => (estado.papel.layout.ventanas || [])[0].escala")

        def dentro_de_la_ventana():
            """Un punto en mm de papel que cae dentro de la ventana 0."""
            return pagina.evaluate("""() => {
                const v = (estado.papel.layout.ventanas || [])[0];
                return [v.x + v.ancho / 2, v.y + v.alto / 2];
            }""")

        def zoom_de_la_hoja():
            return pagina.evaluate("() => estado.vista.escala")

        def rodar(hacia_arriba):
            """Una rueda DE VERDAD sobre el lienzo, en el centro de la ventana.

            Se dispara el evento y no se llama a la función a pelo: el error que
            esto vigila —que `rueda` fuera `async` y devolviera una promesa, que
            siempre es cierta— no vive en la función sino en QUIEN LA LLAMA, en
            `vista.js`. Llamarla directo lo tapa, porque Playwright resuelve la
            promesa antes de devolver el valor.
            """
            pagina.evaluate("""(arriba) => {
                const v = (estado.papel.layout.ventanas || [])[0];
                const [x, y] = aPX(v.x + v.ancho / 2, v.y + v.alto / 2);
                const caja = document.querySelector('#lienzo').getBoundingClientRect();
                estado.cursor.x = v.x + v.ancho / 2;
                estado.cursor.y = v.y + v.alto / 2;
                document.querySelector('#lienzo').dispatchEvent(new WheelEvent('wheel', {
                    clientX: caja.left + x, clientY: caja.top + y,
                    deltaY: arriba ? -100 : 100, bubbles: true, cancelable: true,
                }));
            }""", hacia_arriba)

        r.cierto(esc() > 0, "la hoja tiene su ventana con escala", f"1:{esc()}")

        # 1. CON escala y el modo encendido: la rueda NO la toca.
        pagina.evaluate("() => VentanasHoja.activar(true)")
        pagina.wait_for_timeout(200)
        antes = esc()
        p = dentro_de_la_ventana()
        zoom_antes = zoom_de_la_hoja()
        rodar(True)
        pagina.wait_for_timeout(500)
        r.igual(esc(), antes, "sobre una ventana CON escala, su escala no se movió ni un poco")
        # ÉSTA es la que caza el error de la promesa: si `rueda` fuera `async`,
        # quien la llama vería una promesa —siempre cierta— y se comería la
        # rueda aquí también, dejando la hoja sin acercarse.
        r.cierto(zoom_de_la_hoja() > zoom_antes,
                 "y la rueda cayó donde debía: la HOJA se acercó",
                 f"{zoom_antes:.4f} → {zoom_de_la_hoja():.4f}")

        # 2. Se marca sin escala.
        pagina.evaluate("""async () => {
            await patch('/api/layout/0/ventana/0', {cambios: {sin_escala: true}});
            await Papel.cargar(0);
        }""")
        pagina.wait_for_timeout(500)
        r.cierto(pagina.evaluate("() => !!(estado.papel.layout.ventanas || [])[0].sin_escala"),
                 "la ventana queda marcada sin escala")

        # 3. SIN escala: la rueda sí acerca, y devuelve un booleano de verdad.
        antes = esc()
        zoom_antes = zoom_de_la_hoja()
        rodar(True)
        pagina.wait_for_timeout(800)
        despues = esc()
        r.igual(zoom_de_la_hoja(), zoom_antes,
                "ahora la rueda se la queda la ventana: la hoja NO se acercó")
        r.cierto(despues < antes,
                 "acercar deja ver menos mundo en el mismo papel: la escala baja",
                 f"{antes} → {despues}")

        # 4. Y al revés.
        rodar(False)
        pagina.wait_for_timeout(800)
        r.cierto(esc() > despues, "y alejar la sube", f"{despues} → {esc()}")

        # 5. Con el modo APAGADO no manda, aunque la ventana sea sin escala.
        pagina.evaluate("() => VentanasHoja.activar(false)")
        pagina.wait_for_timeout(200)
        quieta = esc()
        zoom_antes = zoom_de_la_hoja()
        rodar(True)
        pagina.wait_for_timeout(500)
        r.igual(esc(), quieta,
                "con EDITARVENTANA apagado, la ventana sin escala no se mueve")
        r.cierto(zoom_de_la_hoja() > zoom_antes,
                 "y la rueda vuelve a ser la de la hoja",
                 f"{zoom_antes:.4f} → {zoom_de_la_hoja():.4f}")

        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")
