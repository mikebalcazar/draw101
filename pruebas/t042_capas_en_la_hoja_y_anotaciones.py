"""t042 · Las capas se apagan también en la hoja, y la capa ANOTACIONES.

Mike, 29-sep-2026, dos cosas del mismo día:

  «Cuando apago o prendo layers, en el layout de plano no se apagan o prenden.
  Sólo las cotas.»

  «Cuando genero un texto, necesito que también se dibuje directo en el layer
  de cotas, que en vez de llamarse COTAS, ahora que se llame ANOTACIONES.
  Cotas, texto, leaders van dibujadas directo en el layer de anotaciones.»

EL BUG DE LA HOJA no era del motor —se midió: `papel.trazos_papel` filtra por
capa desde siempre— sino de la interfaz. En una hoja lo que se ve tiene DOS
orígenes: lo dibujado sobre la hoja viene de `/api/trazos`, que sí se volvía a
pedir (por eso las cotas respondían), y lo que se ve por las ventanas viene de
`/api/papel/<i>`, que se pedía una sola vez al entrar. Aquí se mide el motor
—que no debe cambiar— y la interfaz —que es lo que se arregló—.

LA CAPA se renombró porque el nombre dejó de describir lo que hay dentro. Al
abrir un `.t101d` viejo su COTAS se renombra sola; un DXF del arquitecto con su
propia COTAS no se toca, que es lo que Mike escogió con botones.
"""

from __future__ import annotations

import pathlib
import tempfile

from pruebas import comun, navegador


DESCRIPCION = "las capas se apagan en la hoja, y cotas/texto nacen en ANOTACIONES"


def correr(r: comun.Reporte) -> None:
    _el_motor(r)
    _la_capa(r)
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: lo de la interfaz se salta)")
        return
    _la_hoja_en_la_interfaz(r)


def _el_motor(r: comun.Reporte) -> None:
    """El motor SIEMPRE filtró bien. Se mide para que siga así: si algún día
    deja de filtrar, el arreglo de la interfaz no lo taparía."""
    from core.documento import Documento
    from core import entidades as E, papel, capas as mod_capas

    doc = Documento()
    doc.capa_agregar(mod_capas.Capa("MUROS", "#FFFFFF", 25, "CONTINUOUS"))
    for y in (0, 500):
        doc.agregar(E.Linea(p1=[0, y], p2=[1000, y], capa="MUROS"))
    L = {"nombre": "PLANO", "ancho": 420, "alto": 297,
         "ventanas": [{"centro": [500, 250], "escala": 50,
                       "x": 20, "y": 20, "ancho": 380, "alto": 250}]}

    def en_la_hoja():
        return sum(1 for t in papel.trazos_papel(doc, L, propias=False)["trazos"]
                   if t["capa"] == "MUROS")

    r.igual(en_la_hoja(), 2, "con la capa encendida, sus trazos salen en la hoja")
    doc.capas["MUROS"].visible = False
    r.igual(en_la_hoja(), 0, "y apagada, el motor no los manda: el filtro nunca estuvo roto")


def _la_capa(r: comun.Reporte) -> None:
    from core.documento import Documento
    from core import entidades as E, capas as mod_capas, cotas as mod_cotas, proyecto

    r.igual(mod_capas.CAPA_ANOTACIONES, "ANOTACIONES", "la capa se llama ANOTACIONES")
    r.igual(sorted(Documento().capas), ["0", "ANOTACIONES"],
            "y un dibujo nuevo nace con ella, no con COTAS")

    d = Documento()
    d.capa_agregar(mod_capas.Capa("MUROS"))
    d.capa_activa = "MUROS"
    texto = mod_cotas.encapar(d, E.Texto(p=[0, 0], texto="nota", capa="MUROS"))
    r.igual(texto.capa, "ANOTACIONES",
            "un TEXTO nace en ANOTACIONES aunque se esté trabajando en MUROS")
    otra = mod_cotas.encapar(d, E.Linea(p1=[0, 0], p2=[1, 1], capa="MUROS"))
    r.igual(otra.capa, "MUROS", "y una línea NO se mueve: sólo las anotaciones")

    # La directriz es una cota de clase «directriz», no una entidad aparte: por
    # eso ya entraba sin tocar nada. Se mide para que no se rompa en silencio.
    r.cierto("cota" in mod_cotas.TIPOS_ANOTACION and "texto" in mod_cotas.TIPOS_ANOTACION,
             "cota y texto están en la lista de lo que nace ahí",
             str(mod_cotas.TIPOS_ANOTACION))

    # Un .t101d viejo: se renombra al abrirlo, con todo y lo que hubiera dentro.
    viejo = Documento(con_plantilla=False)
    viejo.capas["0"] = mod_capas.Capa("0")
    viejo.capa_agregar(mod_capas.Capa("COTAS", "#0000FF", 18, "CONTINUOUS",
                                      descripcion=mod_capas.DESCRIPCION_COTAS_VIEJA))
    viejo.agregar(E.Linea(p1=[0, 0], p2=[1, 1], capa="COTAS"))
    ruta = pathlib.Path(tempfile.mkdtemp()) / "viejo.t101d"
    proyecto.guardar(viejo, ruta)
    abierto = proyecto.abrir(ruta)
    r.igual(sorted(abierto.capas), ["0", "ANOTACIONES"],
            "un .t101d viejo se abre ya con ANOTACIONES: la COTAS se renombró")
    r.igual([e.capa for e in abierto.lista()], ["ANOTACIONES"],
            "y lo que vivía en ella se fue con ella: no quedó nada huérfano")

    # Un DXF ajeno: no se toca. Es lo que Mike escogió.
    ajeno = Documento(con_plantilla=False)
    ajeno.capas["0"] = mod_capas.Capa("0")
    ajeno.capa_agregar(mod_capas.Capa("COTAS", "#FF0000", 25, "CONTINUOUS", descripcion=""))
    r.cierto(not mod_capas.migrar_anotaciones(ajeno, propio=False),
             "la COTAS del arquitecto NO se renombra: es suya, no nuestra")
    r.cierto("COTAS" in ajeno.capas, "y ahí sigue, con su nombre")

    # Con las dos, no se funde nada por su cuenta.
    dos = Documento(con_plantilla=False)
    dos.capas["0"] = mod_capas.Capa("0")
    dos.capa_agregar(mod_capas.Capa("COTAS", "#0000FF", 18, "CONTINUOUS",
                                    descripcion=mod_capas.DESCRIPCION_COTAS_VIEJA))
    dos.capa_agregar(mod_capas.Capa("ANOTACIONES", "#0000FF", 18, "CONTINUOUS"))
    r.cierto(not mod_capas.migrar_anotaciones(dos, propio=True),
             "si el dibujo ya trae las dos, no se fusionan solas: eso se deshace peor que se hace")


def _la_hoja_en_la_interfaz(r: comun.Reporte) -> None:
    """Lo que de verdad reportó Mike: estando DENTRO de la hoja, apagar una capa
    tiene que quitar lo que se ve por la ventana."""
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""() => {
            estado.prefs.osnap = false; estado.prefs.ortho = false;
            estado.prefs.snap_rejilla = false; estado.prefs.dinamica = false;
        }""")
        pagina.wait_for_timeout(200)

        # Una capa con algo dentro, en el modelo.
        pagina.evaluate("""async () => {
            await post('/api/capa', {nombre: 'MUROS', color: '#FFFFFF', grosor: 25, tipo_linea: 'CONTINUOUS'});
            await post('/api/operacion', {accion: 'poner', agregar: [
                {tipo: 'linea', p1: [0, 0], p2: [2000, 0], capa: 'MUROS'},
                {tipo: 'linea', p1: [0, 1000], p2: [2000, 1000], capa: 'MUROS'}]});
            await recargarTrazos();
        }""")
        pagina.wait_for_timeout(400)

        # Una hoja con una ventana que mire a eso.
        pagina.evaluate("""async () => {
            await post('/api/layout', {nombre: 'PLANO', ancho: 420, alto: 297});
        }""")
        pagina.wait_for_timeout(400)
        entro = pagina.evaluate("""async () => {
            try {
                await Papel.entrar(0);
                await new Promise((s) => setTimeout(s, 400));
                return estado.modo === 'papel';
            } catch (e) { return 'ERROR: ' + e.message; }
        }""")
        if not r.cierto(entro is True, "se entra a la hoja", str(entro)):
            return

        def en_la_ventana():
            return pagina.evaluate("""() => (estado.papel && estado.papel.trazos || [])
                .filter((t) => t.capa === 'MUROS').length""")

        antes = en_la_ventana()
        if not r.cierto(antes > 0, "la capa MUROS se ve por la ventana de la hoja", f"{antes} trazos"):
            return

        # Y AQUÍ ESTABA EL BUG: apagarla desde dentro de la hoja.
        pagina.evaluate("""async () => { await cambiarCapa('MUROS', {visible: false}); }""")
        pagina.wait_for_timeout(600)
        r.igual(en_la_ventana(), 0,
                "al apagarla SIN SALIR de la hoja, deja de verse por la ventana")

        pagina.evaluate("""async () => { await cambiarCapa('MUROS', {visible: true}); }""")
        pagina.wait_for_timeout(600)
        r.igual(en_la_ventana(), antes, "y al prenderla vuelve, sin tener que entrar y salir")

        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")
