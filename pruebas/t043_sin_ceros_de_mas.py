"""t043 · Las cotas no escriben los ceros de más.

Mike, 29-sep-2026: «las cotas, quiero que por default eliminen los "trailing
zeros". Si no hay decimales que marcar, no se ponen decimales».

Es el DIMZIN 8 de AutoCAD y es lo normal en un plano de arquitectura: 120 se
lee de un vistazo, 120.00 hay que leerlo.

IMPORTA DESDE QUE EL TALLER TRABAJA EN CENTÍMETROS. En milímetros enteros la
cota va con cero decimales y no había ceros que sobraran; en centímetros hay
que pedir un decimal para no perder los milímetros, y entonces CADA medida
redonda arrastraba un «.0» que no aporta nada.

Tres sitios y los tres se miden, porque si uno se queda atrás el plano dice
una cosa aquí y otra en AutoCAD:

  · el motor, que arma el texto de la cota;
  · el DXF, donde el texto va como «<>» y quien lo formatea es AutoCAD con SU
    estilo — por eso hay que escribirle DIMZIN, no basta con arreglarlo aquí;
  · la pantalla de ajustes, para poder devolver los ceros si alguien los
    quiere. Y que la casilla GUARDE: el servidor tiene una lista blanca de
    campos y lo que no está en ella se ignora en silencio.
"""

from __future__ import annotations

import pathlib
import tempfile

from pruebas import comun, navegador


DESCRIPCION = "las cotas no escriben los ceros de más (el DIMZIN de AutoCAD)"


def correr(r: comun.Reporte) -> None:
    _el_texto(r)
    _el_dxf(r)
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: lo de la pantalla se salta)")
        return
    _la_casilla(r)


def _el_texto(r: comun.Reporte) -> None:
    from core import cotas as mod_cotas

    uno = {"decimales": 1}
    r.igual(mod_cotas.formato(120.0, uno), "120",
            "una medida redonda no arrastra el «.0»")
    r.igual(mod_cotas.formato(120.5, uno), "120.5",
            "y el decimal que SÍ dice algo se queda")

    dos = {"decimales": 2}
    r.igual(mod_cotas.formato(120.0, dos), "120", "con dos decimales, igual")
    r.igual(mod_cotas.formato(120.5, dos), "120.5", "se quita sólo el cero de sobra")
    r.igual(mod_cotas.formato(120.25, dos), "120.25", "y lo que no sobra no se toca")

    r.igual(mod_cotas.formato(0.0, uno), "0", "el cero es «0», no «0.0»")
    r.igual(mod_cotas.formato(-3.50, dos), "-3.5", "y con signo también")

    # Con cero decimales nunca hubo punto: no debe aparecer uno.
    r.igual(mod_cotas.formato(120.0, {"decimales": 0}), "120",
            "con cero decimales sigue saliendo igual que siempre")

    # El sufijo va DESPUÉS de quitar los ceros, o se quitarían sus letras.
    r.igual(mod_cotas.formato(120.0, {"decimales": 2, "sufijo": " cm"}), "120 cm",
            "el sufijo se pega después: quitar los ceros no se come sus letras")

    # El texto que escribe el usuario manda, y «<>» trae la medida ya limpia.
    r.igual(mod_cotas.formato(120.0, uno, "<> APROX"), "120 APROX",
            "y en un texto propio, «<>» trae la medida ya sin los ceros")

    # Se puede apagar: es una casilla, no una imposición.
    apagado = {"decimales": 2, "quitar_ceros": False}
    r.igual(mod_cotas.formato(120.0, apagado), "120.00",
            "apagándolo, vuelven los ceros de siempre")

    # Un dibujo viejo, cuyo estilo no trae la clave, se comporta como los nuevos.
    r.igual(mod_cotas.formato(120.0, {"decimales": 2}), "120",
            "un estilo guardado antes de que esto existiera también los quita")


def _el_dxf(r: comun.Reporte) -> None:
    """Sin DIMZIN en el DXF, AutoCAD volvería a poner los ceros: el texto de la
    cota viaja como «<>» y quien lo formatea allá es AutoCAD."""
    import ezdxf

    from core.documento import Documento
    from core import entidades as ent, cotas as mod_cotas
    from export import dxf as exp

    doc = Documento()
    doc.estilos_cota["T101"]["decimales"] = 1
    with doc.transaccion("Acotar"):
        doc.agregar(mod_cotas.encapar(doc, ent.Cota(
            clase="lineal", puntos=[[0, 0], [1200, 0], [0, -200]])))
    ruta = pathlib.Path(tempfile.mkdtemp()) / "cota.dxf"
    exp.escribir(doc, ruta)

    d = ezdxf.readfile(str(ruta))
    est = d.dimstyles.get("T101")
    r.igual(est.dxf.dimzin, 8,
            "el DXF lleva DIMZIN 8: AutoCAD tampoco escribe los ceros de más")
    r.igual(est.dxf.dimdec, 1, "y los decimales que se pidieron")

    doc.estilos_cota["T101"]["quitar_ceros"] = False
    ruta2 = pathlib.Path(tempfile.mkdtemp()) / "cota2.dxf"
    exp.escribir(doc, ruta2)
    r.igual(ezdxf.readfile(str(ruta2)).dimstyles.get("T101").dxf.dimzin, 0,
            "y si se apaga aquí, se apaga allá: el plano dice lo mismo en los dos lados")


def _la_casilla(r: comun.Reporte) -> None:
    """Que la casilla exista Y QUE GUARDE. El servidor ignora en silencio los
    campos que no están en su lista blanca, así que una casilla nueva puede
    verse, picarse y no hacer nada."""
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.wait_for_timeout(200)

        de_fabrica = pagina.evaluate("""async () => {
            const r = await post('/api/estilo_cota', {nombre: 'T101', cambios: {}});
            return r.estilo.quitar_ceros;
        }""")
        r.cierto(de_fabrica is True, "de fábrica viene encendido", str(de_fabrica))

        guardado = pagina.evaluate("""async () => {
            const r = await post('/api/estilo_cota', {nombre: 'T101', cambios: {quitar_ceros: false}});
            return r.estilo.quitar_ceros;
        }""")
        r.cierto(guardado is False,
                 "y apagarlo SE GUARDA: la clave está en la lista blanca del servidor",
                 str(guardado))

        vuelta = pagina.evaluate("""async () => {
            const r = await post('/api/estilo_cota', {nombre: 'T101', cambios: {quitar_ceros: true}});
            return r.estilo.quitar_ceros;
        }""")
        r.cierto(vuelta is True, "y se puede volver a encender", str(vuelta))

        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")
