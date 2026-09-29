"""t045 · El espacio acepta la respuesta; no la borra.

Mike, 29-sep-2026: «cuando hago mirror, que doy enter y pregunta si borro el
original y escribo N o Y... si uso espacio borra la N pero no activa el
comando. Recuerda que el espacio no sirve para nada más que de "enter",
desactiva el espacio como carácter a la hora que hay ventanas de comandos».

UN MATIZ QUE SÍ IMPORTA: la regla no puede ser literal. El texto de un rótulo,
el nombre de un bloque o la ruta de una carpeta necesitan espacios de verdad —
«dos palabras» son dos palabras. Lo que se arregla es la pregunta de
RESPUESTA (S/N, R/P), donde el espacio debe aceptar como Enter.

`Entrada.pedirTexto` ya sabía hacerlo: con `opciones` pone `libre` en falso y
el espacio confirma. Faltaba declararlas en tres preguntas. Por eso la prueba
tiene dos mitades:

  · un RASTREO del código: toda pregunta con forma «X/Y» declara `opciones`
    (o `libre: false`), con aserciones de control para que el rastreo no pueda
    pasar por no haber mirado nada;
  · un ESPEJO de verdad: se teclea la respuesta, se da ESPACIO, y el comando
    tiene que terminar. Se mira el ESTADO y no el texto, porque el banco de
    pruebas corre la interfaz en inglés («Erase the original? Y/N»).

Eso último destapó un segundo defecto: en inglés el sí se contesta con Y, y el
código sólo miraba la S. Se aceptan las dos.
"""

from __future__ import annotations

import os
import re

from pruebas import comun, navegador


DESCRIPCION = "el espacio acepta la respuesta de una pregunta S/N, y no la borra"

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(RAIZ, "ui")

# Una pregunta de respuesta: «...? S/N», «...? R/P», «... Y/N».
FORMA_RESPUESTA = re.compile(r"\b[A-ZÁÉÍÓÚ]\s*/\s*[A-ZÁÉÍÓÚ]\b")


def correr(r: comun.Reporte) -> None:
    _el_rastreo(r)
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: lo del espejo se salta)")
        return
    _el_espejo(r)


# --------------------------------------------------------------------------
# 1 · El rastreo del código
# --------------------------------------------------------------------------

def _llamadas(texto: str):
    """(mensaje, cuerpo) por cada `pedirTexto({...})`.

    Cuenta llaves en vez de cortar a la primera `}`: varios mensajes llevan
    plantillas `${...}` dentro y se partirían a la mitad."""
    salida = []
    for m in re.finditer(r"pedirTexto\(\s*\{", texto):
        i = m.end() - 1
        hondo, j = 0, i
        while j < len(texto):
            if texto[j] == "{":
                hondo += 1
            elif texto[j] == "}":
                hondo -= 1
                if hondo == 0:
                    break
            j += 1
        cuerpo = texto[i:j + 1]
        men = re.search(r"mensaje\s*:\s*([\"'`])(.*?)\1", cuerpo, re.S)
        salida.append((men.group(2) if men else "", cuerpo))
    return salida


def _el_rastreo(r: comun.Reporte) -> None:
    vistas, respuesta, peladas = 0, [], []
    for nombre in sorted(os.listdir(UI)):
        if not nombre.endswith(".js"):
            continue
        with open(os.path.join(UI, nombre), encoding="utf-8") as f:
            texto = f.read()
        for mensaje, cuerpo in _llamadas(texto):
            vistas += 1
            if not FORMA_RESPUESTA.search(mensaje):
                continue
            respuesta.append((nombre, mensaje))
            if not (("opciones" in cuerpo) or re.search(r"libre\s*:\s*false", cuerpo)):
                peladas.append(nombre + ": " + mensaje)

    # Control: un rastreo que no encuentra nada pasaría siempre.
    r.cierto(vistas > 10, "el rastreo sí está leyendo llamadas a pedirTexto",
             "%d llamadas" % vistas)
    r.cierto(len(respuesta) >= 3, "y encuentra preguntas de respuesta X/Y",
             "%d preguntas" % len(respuesta))
    r.igual(peladas, [], "ninguna pregunta X/Y se queda sin opciones")

    hallados = " | ".join(x[1] for x in respuesta)
    for esperada in ("Borrar el original", "Rectangular o Polar",
                     "Acotar automáticamente"):
        r.cierto(esperada in hallados,
                 "la pregunta «%s» entra en el rastreo" % esperada)


# --------------------------------------------------------------------------
# 2 · El espejo de verdad
# --------------------------------------------------------------------------

def _linea(pagina) -> None:
    pagina.evaluate("""async () => {
        const ids = (estado.trazos || []).map(t => t.id);
        if (ids.length) await post('/api/operacion', {accion: 'limpiar', borrar: ids});
        await post('/api/operacion', {accion: 'poner',
            agregar: [{tipo: 'linea', p1: [0, 0], p2: [400, 0]}]});
        await recargarTrazos(); Seleccion.limpiar(); }""")
    pagina.wait_for_timeout(300)


def _espejo(pagina, respuesta: str, tecla: str):
    """ESPEJO hasta la pregunta; contesta y confirma con `tecla`.

    Devuelve cómo estaba la pregunta ANTES de contestarla."""
    pagina.click("#cmd")
    pagina.type("#cmd", "ESPEJO", delay=10)
    pagina.keyboard.press("Enter")
    pagina.wait_for_timeout(300)
    x, y = pagina.evaluate("""() => { const [x, y] = aPX(200, 0);
        const c = document.querySelector('#lienzo').getBoundingClientRect();
        return [c.left + x, c.top + y]; }""")
    pagina.mouse.move(x, y)
    pagina.wait_for_timeout(100)
    pagina.mouse.click(x, y)
    pagina.wait_for_timeout(250)
    pagina.keyboard.press("Enter")            # cierra la selección
    pagina.wait_for_timeout(250)
    for p in ("0,500", "400,500"):            # el eje del espejo
        pagina.click("#cmd")
        pagina.type("#cmd", p, delay=10)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(300)
    estado = (pagina.evaluate("() => Entrada.esperandoTexto"),
              pagina.evaluate("() => Entrada.esperandoTextoLibre"))
    pagina.click("#cmd")
    pagina.type("#cmd", respuesta, delay=20)
    pagina.keyboard.press(tecla)
    pagina.wait_for_timeout(600)
    return estado


def _cuantos(pagina) -> int:
    return pagina.evaluate("() => (estado.trazos || []).length")


def _el_espejo(r: comun.Reporte) -> None:
    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""() => { estado.prefs.osnap = false;
            estado.prefs.ortho = false; estado.prefs.snap_rejilla = false;
            estado.prefs.dinamica = false;
            encuadrarCaja(-500, -500, 1500, 1500); }""")
        pagina.wait_for_timeout(200)

        # 1 · La pregunta llega, y NO es de texto libre: ahí está el arreglo.
        _linea(pagina)
        esperando, libre = _espejo(pagina, "N", "Space")
        r.igual(esperando, True, "ESPEJO sí llega a preguntar si se borra el original")
        r.igual(libre, False,
                "y la pregunta no es de texto libre, así que el espacio acepta")

        # 2 · El espacio cerró la pregunta, que es justo lo que Mike reportó.
        r.igual(pagina.evaluate("() => Entrada.esperandoTexto"), False,
                "el espacio acepta la respuesta en vez de borrarla")
        r.igual(_cuantos(pagina), 2, "y con N se quedan original y copia")

        # 3 · Lo mismo contestando que sí.
        _linea(pagina)
        _espejo(pagina, "S", "Space")
        r.igual(pagina.evaluate("() => Entrada.esperandoTexto"), False,
                "con S el espacio también acepta")
        r.igual(_cuantos(pagina), 1, "y con S se borra el original")

        # 4 · En inglés la pregunta sale «Y/N»: la Y tiene que valer igual.
        _linea(pagina)
        _espejo(pagina, "Y", "Space")
        r.igual(_cuantos(pagina), 1,
                "la Y borra igual que la S (en inglés la pregunta dice Y/N)")

        # 5 · Y el Enter de toda la vida sigue sirviendo.
        _linea(pagina)
        _espejo(pagina, "N", "Enter")
        r.igual(pagina.evaluate("() => Entrada.esperandoTexto"), False,
                "el Enter sigue aceptando")
        r.igual(_cuantos(pagina), 2, "con Enter y N se queda el original")

        # 6 · Un rótulo de verdad sigue llevando espacios. La regla no es literal.
        escrito = pagina.evaluate("""async () => {
            const p = Entrada.pedirTexto({ mensaje: 'Texto' });
            await new Promise(res => setTimeout(res, 80));
            const c = document.querySelector('#cmd'); c.focus();
            for (const ch of 'dos palabras') {
                c.value += ch;
                c.dispatchEvent(new KeyboardEvent('keydown',
                    {key: ch, bubbles: true, cancelable: true}));
            }
            c.dispatchEvent(new KeyboardEvent('keydown',
                {key: 'Enter', bubbles: true, cancelable: true}));
            return await p; }""")
        r.igual(escrito, "dos palabras",
                "un rótulo sigue admitiendo espacios de verdad")

        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")
