"""t054 · La nube en la pantalla de inicio, apretada de verdad con Playwright.

Mike lo pidió así, con palabras suyas (1-oct-2026): «En la pantalla inicial,
quiero ver los archivos recientes y también los archivos en la nube, a lo mejor
son 2 ventanas diferentes, pero quiero poder explorar los archivos de la nube
cuando abro por si quiero trabajar en alguno».

LO QUE ESTA PRUEBA DEFIENDE, QUE NO ES LA COLUMNA

La columna se ve de un vistazo; si faltara, se nota en un segundo. Lo que no se
ve, y es lo que aquí se mide, es que esa columna sea **el mismo código** del
cuadro NUBE y no una segunda lista escrita aparte. Una copia habría nacido sin
el buscador sin acentos, sin las palabras en cualquier orden, sin los cuatro
órdenes y sin los cinco avisos —todo eso es trabajo medido de t050— y nadie se
habría dado cuenta hasta que alguien buscara «ramirez» desde el inicio y no
encontrara su plano. Por eso varias comprobaciones de aquí repiten a propósito
cosas que t050 ya mide: aquí no se mide la función, se mide QUE SEA LA MISMA.

Y LOS DOS ESTADOS SON SEPARADOS, que es la otra decisión. Si la lista del inicio
y la del cuadro NUBE compartieran lo que se busca y cómo se ordena, teclear en
una movería la otra a espaldas de uno. Se comprueba en las dos direcciones, con
un control de que las dos listas empezaron iguales: sin ese control, la
comprobación pasaría igual si una de las dos estuviera vacía.

ABRIR DESDE AHÍ CIERRA LA PANTALLA DE INICIO. Suena a detalle y no lo es: sin
eso, picar «Abrir» baja el plano, lo abre, y lo deja tapado por la pantalla de
inicio que sigue encima. Parecería que no pasó nada.

UN PELIGRO QUE ESTA PRUEBA DESTAPÓ Y QUE VALE MÁS QUE SUS COMPROBACIONES:
t050 buscaba `.nube-fila` y `.nube-aviso` en todo el documento. Como `#inicio`
va primero en el index.html, en cuanto esta columna existió esas consultas
empezaban a encontrar la lista del inicio en vez de la del cuadro — y t050
habría seguido en verde midiendo la pantalla equivocada. Cerrar la pantalla de
inicio no salva: cerrarla sólo le quita una clase, su HTML se queda. Por eso
t050 va acotada a `.dlg.nube` y esta prueba a `#iNube`.

VERIFICADA ROMPIENDO EL CÓDIGO, una por una, y con los números medidos:

  · sin montar la columna → 1 comprobación que falla diciendo exactamente eso,
    y la prueba se corta ahí en vez de reventar;
  · compartiendo el estado entre las dos listas → 2;
  · sin cerrar la pantalla de inicio al abrir un plano → 1;
  · pidiendo el índice en cada letra tecleada → 1 (9 peticiones esperadas, 15);
  · dejando la columna visible aunque la versión no traiga nube → 1.

Y DOS COSAS QUE ESTA PRUEBA APRENDIÓ DE SÍ MISMA, porque la primera versión las
tenía mal y sólo se vieron al romperla a propósito:

  1. LA INDEPENDENCIA NO SE MIDE MIRANDO EL DOM DE LA OTRA LISTA. Con el estado
     compartido a propósito, t054 seguía en verde: al teclear en una, la otra no
     se repinta, así que su DOM viejo seguía en pantalla y parecía intacto. Hay
     que OBLIGARLA A REPINTARSE —picar uno de sus órdenes— y entonces sí falla.
  2. SIN LA COLUMNA, LA PRUEBA REVENTABA en vez de reportar, y una prueba que
     lanza una excepción se come el armado entero en vez de decir qué pasó. Ya
     costó dos veces en las pruebas de la nube. Ahora `_remontar` lo reporta.
"""

from __future__ import annotations

from pruebas import comun, navegador

DESCRIPCION = "la nube en la pantalla de inicio: es la misma lista del cuadro NUBE, con su propio estado"


# La misma lista que usa t050, a propósito: si las dos pantallas son el mismo
# código, los mismos datos tienen que dar los mismos resultados.
LISTA = """[
  { token: 'AAA0000000000000000000000A', nombre: 'Cocina Ramírez.t101d', bytes: 4096,
    version: 2, creado: '2026-01-10T10:00:00Z', modificado: '2026-09-28T10:00:00Z',
    subido: '2026-09-28T10:00:05Z', equipo: 'la-de-mike', aperturas: 2, abierto: null },
  { token: 'BBB0000000000000000000000B', nombre: 'Closet Ruiz.t101d', bytes: 900000,
    version: 1, creado: '2026-08-01T10:00:00Z', modificado: '2026-02-02T10:00:00Z',
    subido: '2026-02-02T10:00:05Z', equipo: 'la-de-mike', aperturas: 40, abierto: null },
  { token: 'CCC0000000000000000000000C', nombre: 'Baño Ruiz etapa 2.t101d', bytes: 2048,
    version: 5, creado: '2026-05-05T10:00:00Z', modificado: '2026-07-07T10:00:00Z',
    subido: '2026-07-07T10:00:05Z', equipo: 'la-de-fer', aperturas: 0, abierto: null }
]"""

# Todo lo de aquí va acotado a `#iNube`: ver la cabecera.
NOMBRES_INICIO = ("() => [...document.querySelectorAll('#iNube .nube-fila .nube-nom')]"
                  ".map(n => n.textContent)")
NOMBRES_CUADRO = ("() => [...document.querySelectorAll('.dlg.nube .nube-fila .nube-nom')]"
                  ".map(n => n.textContent)")
POR_INICIO = ("() => { const a = document.querySelector('#iNube .nube-aviso');"
              " return !a || a.hidden ? null : (a.dataset.por || ''); }")


def _puente(pagina, lista_js: str) -> None:
    """El puente de mentiras, puesto ANTES de montar la columna."""
    pagina.evaluate("""(lista) => {
        window.espia = { indiceYa: 0, indiceBajar: 0, bajar: [] };
        window.t101 = window.t101 || {};
        window.respuestaYa = { archivos: lista, de_cache: true };
        window.respuestaRed = { archivos: lista, al: '2026-10-01T20:00:00Z' };
        window.t101.nube = {
          indiceYa: async () => { window.espia.indiceYa++; return window.respuestaYa; },
          indiceBajar: async () => { window.espia.indiceBajar++; return window.respuestaRed; },
          bajar: async (doc) => { window.espia.bajar.push(doc);
                                  return { ok: true, ruta: 'C:/de-la-nube/' + doc + '.t101d' }; },
          quitar: async () => ({ ok: true }),
          encendida: async () => true, prender: async () => true, alLlegarIndice: () => {},
        };
        window.abiertos = [];
        Archivo.abrir = async (ruta) => { window.abiertos.push(ruta); return true; };
    }""", pagina.evaluate("() => " + lista_js))


def _remontar(pagina, r=None, esperar_filas: bool = True) -> bool:
    """Vuelve a abrir la pantalla de inicio, que es lo que monta la columna.

    Devuelve si la columna llego a montarse. NO revienta cuando no: una prueba
    que lanza una excepcion se come el armado entero en vez de decir que paso,
    y eso ya costo dos veces en las pruebas de la nube. Si la columna no esta,
    se reporta como una comprobacion que FALLA y la prueba se corta ahi.
    """
    from playwright.sync_api import Error as ErrorPW, TimeoutError as TiempoPW
    pagina.evaluate("() => { Marco.cerrarInicio(); Marco.abrirInicio(); }")
    try:
        pagina.wait_for_selector("#iNube .nube-busca", timeout=4000)
        if esperar_filas:
            pagina.wait_for_function(
                "() => document.querySelectorAll('#iNube .nube-fila').length > 0", timeout=4000)
    except (TiempoPW, ErrorPW) as e:
        if r is not None:
            r.cierto(False, "la columna de la nube se monta en la pantalla de inicio",
                     str(e).splitlines()[0][:180])
        return False
    return True


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: se salta)")
        return

    with navegador.programa() as (pagina, base):
        _puente(pagina, LISTA)
        if not _remontar(pagina, r):
            return          # sin columna no hay nada que medir, y ya se reporto

        # --- 1. La columna está, y es la de verdad -----------------------
        r.cierto(pagina.evaluate("() => !document.querySelector('#iEnNube').hidden"),
                 "la columna «En la nube» sale en la pantalla de inicio")
        r.cierto(pagina.evaluate("() => !!document.querySelector('#iNube .nube-busca')"),
                 "y trae su buscador")
        r.igual(pagina.evaluate(
            "() => [...document.querySelectorAll('#iNube .nube-ordenes .gh')].map(b => b.dataset.orden)"),
            ["modificado", "creado", "nombre", "aperturas"],
            "y los cuatro órdenes, con su clave en un dato y no sólo en la etiqueta")
        r.igual(len(pagina.evaluate(NOMBRES_INICIO)), 3,
                "y pinta los tres planos de la lista")

        # --- 2. Es el MISMO código, no una copia -------------------------
        # Si alguien escribiera aquí una lista aparte, nacería sin esto.
        pagina.fill("#iNube .nube-busca", "ramirez")
        r.igual(pagina.evaluate(NOMBRES_INICIO), ["Cocina Ramírez"],
                "buscar «ramirez» sin acento encuentra «Ramírez», igual que en el cuadro NUBE")

        pagina.fill("#iNube .nube-busca", "ruiz baño")
        r.igual(pagina.evaluate(NOMBRES_INICIO), ["Baño Ruiz etapa 2"],
                "y las palabras en cualquier orden: «ruiz baño» encuentra «Baño Ruiz etapa 2»")

        pagina.fill("#iNube .nube-busca", "zzzz")
        # Sin este control, las dos comprobaciones de arriba pasarían aunque el
        # buscador no filtrara nada.
        r.igual(pagina.evaluate(NOMBRES_INICIO), [],
                "CONTROL · algo que no existe deja la lista vacía")
        r.cierto(pagina.evaluate("() => !!document.querySelector('#iNube .nube-vacio')"),
                 "y lo dice en vez de dejar un hueco")

        pagina.fill("#iNube .nube-busca", "")
        r.igual(len(pagina.evaluate(NOMBRES_INICIO)), 3, "y al borrar la búsqueda vuelven los tres")

        # --- 2b. CÓMO SE ESCRIBEN LA FECHA Y EL TAMAÑO -------------------
        # Esto parece cosmético y es el candado de una trampa real: al sacar el
        # explorador a una función aparte, `cuando()` y `pesa()` se reescribieron
        # de memoria en vez de moverse, y quedaron distintas de las originales
        # («hace 3 días» en vez de «hace 3 d», KB con decimal en vez de entero).
        # NINGUNA prueba lo cazó, porque ninguna miraba el texto. Se encontró
        # leyendo el diff a mano. Esto lo fija para que la próxima no dependa de
        # que alguien lea con cuidado.
        pagina.evaluate("""() => {
            const hace = (d) => new Date(Date.now() - d * 86400000).toISOString();
            const uno = [{ token: 'EEE0000000000000000000000E', nombre: 'Medidas.t101d',
                           bytes: 4096, version: 1, creado: hace(9), modificado: hace(3),
                           subido: hace(3), equipo: null, aperturas: 0, abierto: null }];
            window.respuestaYa = { archivos: uno, de_cache: true };
            window.respuestaRed = { archivos: uno, al: hace(0) };
        }""")
        if _remontar(pagina, r):
            # Las dos formas, porque EL IDIOMA LO DECIDE EL MOTOR y no el
            # navegador: la app sale en inglés de fábrica. Lo que se fija es el
            # FORMATO —«3 d» y no «3 días», KB entero y no con decimal—, que es
            # lo que se había reescrito sin querer.
            r.cierto(pagina.evaluate(
                "() => document.querySelector('#iNube .nube-dat').textContent")
                in ("hace 3 d · 4 KB", "3 d ago · 4 KB"),
                "la fecha y el tamaño se escriben como siempre: «3 d» (no «3 días») y los KB enteros",
                pagina.evaluate("() => document.querySelector('#iNube .nube-dat').textContent"))

        # Se devuelve la lista de siempre para lo que sigue.
        pagina.evaluate("(l) => { window.respuestaYa = { archivos: l, de_cache: true };"
                        " window.respuestaRed = { archivos: l, al: '2026-10-01T20:00:00Z' }; }",
                        pagina.evaluate("() => " + LISTA))
        if not _remontar(pagina, r):
            return

        # --- 3. Cada lista tiene su propio estado ------------------------
        # Se abre por codigo y no tecleando «NUBE»: con la pantalla de inicio
        # encima, la linea de comandos no se alcanza — y eso esta bien asi. Lo
        # que aqui se mide es que DOS listas montadas a la vez no se pisen el
        # estado, no por donde se abre la segunda.
        pagina.evaluate("() => Nube.abrir()")
        pagina.wait_for_selector(".dlg.nube .nube-busca", timeout=4000)
        pagina.wait_for_function(
            "() => document.querySelectorAll('.dlg.nube .nube-fila').length > 0", timeout=4000)

        # Si el cuadro empezara vacío, la comprobación de independencia de abajo
        # pasaría sin medir nada.
        r.igual(len(pagina.evaluate(NOMBRES_CUADRO)), 3,
                "CONTROL · el cuadro NUBE empieza con los mismos tres")

        pagina.fill(".dlg.nube .nube-busca", "closet")
        r.igual(pagina.evaluate(NOMBRES_CUADRO), ["Closet Ruiz"],
                "buscar en el cuadro NUBE filtra el cuadro NUBE")
        r.igual(len(pagina.evaluate(NOMBRES_INICIO)), 3,
                "y NO mueve la lista de la pantalla de inicio")

        # Y AQUI ESTA LA COMPROBACION QUE DE VERDAD MIDE. Mirar el DOM de la otra
        # lista no basta: con el estado compartido, la otra lista NO se repinta
        # al teclear en esta, asi que su DOM viejo sigue en pantalla y la prueba
        # pasaria igual. Medido: con `busca` compartido a proposito, las dos
        # comprobaciones de arriba seguian en verde. Hay que OBLIGARLA A
        # REPINTARSE —picar uno de sus ordenes— y ver que sigue completa.
        # Por codigo y no con un clic de verdad: el cuadro NUBE esta encima y se
        # queda con el clic. Lo que se mide es el repintado, no el raton.
        pagina.evaluate("() => document.querySelector("
                        "'#iNube .nube-ordenes .gh[data-orden=nombre]').click()")
        r.igual(len(pagina.evaluate(NOMBRES_INICIO)), 3,
                "y al repintarse sigue completa: lo que se busca en una no es lo de la otra")
        r.igual(pagina.evaluate(
            "() => document.querySelector('#iNube .nube-busca').value"), "",
            "CONTROL · su buscador tampoco se llenó solo con lo del otro")

        pagina.fill("#iNube .nube-busca", "cocina")
        r.igual(pagina.evaluate(NOMBRES_INICIO), ["Cocina Ramírez"],
                "y al revés: buscar en el inicio filtra el inicio")
        pagina.evaluate("() => document.querySelector("
                        "'.dlg.nube .nube-ordenes .gh[data-orden=nombre]').click()")
        r.igual(pagina.evaluate(NOMBRES_CUADRO), ["Closet Ruiz"],
                "y el cuadro NUBE, repintado, se queda con lo suyo")

        pagina.evaluate("() => Nube.cerrar()")
        pagina.fill("#iNube .nube-busca", "")

        # --- 4. Buscar no le pide nada al servidor -----------------------
        antes = pagina.evaluate("() => window.espia.indiceBajar")
        r.cierto(antes >= 1,
                 "CONTROL · el espía SÍ contó la carga inicial",
                 "si contara cero, la comprobación de abajo no mediría nada")
        for letra in "cocina":
            pagina.fill("#iNube .nube-busca", letra)
        # Si cada letra preguntara, el servidor sabría qué se busca y la pantalla
        # se sentiría pegajosa.
        r.igual(pagina.evaluate("() => window.espia.indiceBajar"), antes,
                "teclear en el buscador no le pide nada al servidor")
        pagina.fill("#iNube .nube-busca", "")

        # --- 5. Abrir uno desde ahí --------------------------------------
        pagina.evaluate("""() => { [...document.querySelectorAll('#iNube .nube-fila')]
            .find((f) => f.querySelector('.nube-nom').textContent === 'Closet Ruiz')
            .querySelector('button').click(); }""")
        pagina.wait_for_function("() => window.abiertos.length > 0", timeout=4000)

        r.igual(pagina.evaluate("() => window.espia.bajar"), ["BBB0000000000000000000000B"],
                "picar «Abrir» baja ESE archivo y no otro")
        r.igual(pagina.evaluate("() => window.abiertos"),
                ["C:/de-la-nube/BBB0000000000000000000000B.t101d"],
                "y lo abre por la misma puerta que cualquier plano")
        r.cierto(not pagina.evaluate("() => Marco.inicioAbierto()"),
                 "y la pantalla de inicio se quita",
                 "si se quedara encima, taparía justo el plano que se acaba de pedir")

        # --- 6. Se suelta al cerrar y se vuelve a montar -----------------
        pedidos = pagina.evaluate("() => window.espia.indiceBajar")
        _remontar(pagina)
        r.cierto(pagina.evaluate("() => window.espia.indiceBajar") > pedidos,
                 "volver a la pantalla de inicio vuelve a preguntar por el índice",
                 "una lista que se arma una sola vez al arrancar enseñaría planos de hace horas")

        # Una respuesta que llega TARDE, después de cerrar, no debe pintar nada.
        pagina.evaluate("""() => {
            window.t101.nube.indiceBajar = () => new Promise((ok) => {
              window.soltarTarde = () => ok({ archivos: [], sinRed: true });
            });
        }""")
        pagina.evaluate("() => { Marco.cerrarInicio(); Marco.abrirInicio(); }")
        pagina.evaluate("() => Marco.cerrarInicio()")
        pagina.evaluate("() => window.soltarTarde && window.soltarTarde()")
        pagina.wait_for_timeout(120)
        r.cierto(pagina.evaluate(POR_INICIO) is None,
                 "una respuesta del servidor que llega después de cerrar no pinta sobre la pantalla")

        # --- 7. Los avisos, también aquí ---------------------------------
        for respuesta, esperado, que in [
            ("{ archivos: [], apagada: true }", "apagada", "la nube apagada se dice"),
            ("{ archivos: window.laLista, sinRed: true }", "sin_red", "«no se pudo llegar» se dice"),
            ("{ archivos: [], todavia_no: true }", "todavia_no", "«todavía no pude preguntar» se dice"),
        ]:
            pagina.evaluate("(l) => { window.laLista = l; }", pagina.evaluate("() => " + LISTA))
            pagina.evaluate(f"""() => {{
                window.respuestaYa = {respuesta};
                window.t101.nube.indiceBajar = async () => ({respuesta});
            }}""")
            _remontar(pagina) if esperado == "sin_red" else pagina.evaluate(
                "() => { Marco.cerrarInicio(); Marco.abrirInicio(); }")
            pagina.wait_for_function(
                f"() => {{ const a = document.querySelector('#iNube .nube-aviso');"
                f" return a && !a.hidden && a.dataset.por === '{esperado}'; }}", timeout=4000)
            r.igual(pagina.evaluate(POR_INICIO), esperado, que)

        # Sin red, la lista NO se queda vacía: se enseña la de la última vez.
        r.igual(len(pagina.evaluate(NOMBRES_INICIO)), 0,
                "CONTROL · con «todavía no» la lista sí está vacía, que es lo correcto")

        # --- 8. Una versión sin nube no enseña una columna vacía ---------
        pagina.evaluate("() => { window.__nube = window.Nube; window.Nube = undefined; }")
        pagina.evaluate("() => { Marco.cerrarInicio(); Marco.abrirInicio(); }")
        r.cierto(pagina.evaluate("() => document.querySelector('#iEnNube').hidden"),
                 "sin nube en esta versión, la columna no sale",
                 "una columna «En la nube» siempre en blanco se lee como que la nube está rota")
        r.cierto(pagina.evaluate("() => !!document.querySelector('#iRecientes')")
                 and pagina.evaluate("() => Marco.inicioAbierto()"),
                 "CONTROL · y el resto de la pantalla de inicio sigue ahí")
        pagina.evaluate("() => { window.Nube = window.__nube; }")
