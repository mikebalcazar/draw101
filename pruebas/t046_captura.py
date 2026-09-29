"""t046 · CAPTURA (SS): el dibujo al portapapeles.

Mike, 29-sep-2026: «necesito un comando de screenshot que ponga en el
portapapeles un screenshot de la ventana de modelo» y «el shortcut podría ser
SS».

Tres cosas que se miden, porque son las tres que se pueden romper solas:

  · el comando existe con su atajo SS y no le pisa el alias a nadie;
  · la imagen sale con FONDO. El lienzo es transparente; una captura sin
    fondo, pegada en Word o en un correo, sale negra. Aquí se comprueba que
    la esquina trae el color del tema y no un pixel vacío;
  · la mira y los agarres de la selección NO salen. Viven en el lienzo de
    encima y no se copian a propósito: lo que se pega en una cotización es el
    plano, no la foto de alguien trabajando.

El portapapeles de verdad no se puede leer desde el banco de pruebas (hace
falta permiso del navegador), así que se intercepta el puente: se comprueba
que le llega un PNG de verdad, con sus medidas, y no un lienzo en blanco.
"""

from __future__ import annotations

import base64
import struct

from pruebas import comun, navegador


DESCRIPCION = "CAPTURA (SS) copia el dibujo al portapapeles, con fondo y sin la mira"


def correr(r: comun.Reporte) -> None:
    if not navegador.hay_navegador():
        r.cierto(True, "(sin Playwright en esta máquina: se salta)")
        return

    with navegador.programa() as (pagina, base):
        navegador.cerrar_inicio(pagina)
        pagina.evaluate("""() => { estado.prefs.osnap = false;
            estado.prefs.ortho = false; estado.prefs.snap_rejilla = false;
            encuadrarCaja(-500, -500, 1500, 1500); }""")
        pagina.wait_for_timeout(200)

        # 1 · El comando y su atajo.
        # `de` busca en la lista como lo hace la línea de comandos: por nombre
        # o por alias, sin distinguir mayúsculas.
        de = """(a) => { const t = a.toUpperCase();
            const c = Comandos.lista.find(x => x.nombre === t
                || (x.alias || []).some(y => y.toUpperCase() === t));
            return c ? c.nombre : null; }"""
        r.cierto(pagina.evaluate("() => Comandos.existe('CAPTURA')"),
                 "el comando CAPTURA existe")
        for atajo in ("SS", "SCREENSHOT"):
            r.igual(pagina.evaluate(de, atajo), "CAPTURA",
                    "%s lleva a CAPTURA" % atajo)

        # Y no le quitó el alias a nadie: ESCALAR sigue siendo SC.
        r.igual(pagina.evaluate(de, "SC"), "ESCALAR",
                "SC sigue siendo ESCALAR: el atajo nuevo no pisó a nadie")

        # 2 · Se pone algo que dibujar y se espía el puente.
        pagina.evaluate("""async () => {
            await post('/api/operacion', {accion: 'poner', agregar: [
                {tipo: 'linea', p1: [0, 0], p2: [400, 300]},
                {tipo: 'circulo', c: [200, 150], r: 120}]});
            await recargarTrazos(); encuadrar(); }""")
        pagina.wait_for_timeout(500)

        pagina.evaluate("""() => {
            window.__capturado = null;
            window.t101 = Object.assign({}, window.t101 || {}, {
                copiarImagen: (url) => { window.__capturado = url; return true; } });
        }""")

        # Con la selección puesta y la mira encima: nada de eso debe salir.
        pagina.evaluate("""() => {
            estado.seleccion = (estado.trazos || []).map(t => t.id);
            Seleccion.refrescar();
            estado.cursor = Object.assign(estado.cursor || {}, {px: 200, py: 200});
            pintar(); }""")
        pagina.wait_for_timeout(300)
        r.cierto(pagina.evaluate("() => (estado.seleccion || []).length > 0"),
                 "hay algo seleccionado (y con agarres pintados) al capturar")

        pagina.evaluate("() => Comandos.correr('SS')")
        pagina.wait_for_timeout(900)

        url = pagina.evaluate("() => window.__capturado")
        r.cierto(isinstance(url, str) and url.startswith("data:image/png;base64,"),
                 "al puente le llega un PNG",
                 (url or "")[:30])

        # 3 · Es un PNG de verdad, con las medidas del lienzo.
        crudo = base64.b64decode(url.split(",", 1)[1])
        r.igual(crudo[:8], b"\x89PNG\r\n\x1a\n", "y trae la firma de un PNG")
        ancho, alto = struct.unpack(">II", crudo[16:24])
        esperado = pagina.evaluate("() => [lienzo.width, lienzo.height]")
        r.igual([ancho, alto], esperado,
                "y mide lo mismo que el lienzo del dibujo")
        r.cierto(len(crudo) > 2000, "y pesa lo que pesa un dibujo, no un lienzo vacío",
                 "%d bytes" % len(crudo))

        # 4 · El fondo. El lienzo es transparente por su cuenta: quien lo
        #     rellena al pintar es `pintar()`, y quien lo rellena al capturar
        #     es CAPTURA. Para medir SÓLO lo segundo se deja el lienzo
        #     transparente a propósito y se captura sin repintar: si el PNG
        #     sale opaco, el relleno lo puso la captura.
        pagina.evaluate("""() => { lienzo.getContext('2d')
            .clearRect(0, 0, lienzo.width, lienzo.height);
            window.__capturado = null; }""")
        pagina.evaluate("() => Comandos.correr('SS')")
        pagina.wait_for_timeout(700)
        esquina = pagina.evaluate("""async () => {
            const img = new Image();
            await new Promise(r => { img.onload = r; img.src = window.__capturado; });
            const c = document.createElement('canvas');
            c.width = img.width; c.height = img.height;
            const x = c.getContext('2d');
            x.drawImage(img, 0, 0);
            const d = x.getImageData(2, 2, 1, 1).data;
            return [d[0], d[1], d[2], d[3]]; }""")
        r.igual(esquina[3], 255,
                "la captura pone fondo ella misma: pegada en Word no sale negra")
        r.cierto(esquina[0] > 200 and esquina[1] > 200 and esquina[2] > 200,
                 "y es el blanco del tema claro", str(esquina))

        # 5 · Lo del lienzo de encima no se copia. Se le pinta una marca de
        #     un color que no existe en el dibujo y se arma la imagen EN EL
        #     MISMO turno: el bucle de cuadros limpia ese lienzo sesenta veces
        #     por segundo y borraría la marca antes de medir nada.
        hay_marca = pagina.evaluate("""async () => {
            pintar();
            await new Promise(r => requestAnimationFrame(() => r()));
            const e = encima.getContext('2d');
            e.save(); e.setTransform(1, 0, 0, 1, 0, 0);
            e.fillStyle = 'rgb(255,0,255)';
            e.fillRect(0, 0, 60, 60);
            e.restore();
            // Sin ceder a otro cuadro: la composición va aquí mismo.
            const { lienzo: cv } = await _imagenDelModelo();
            const d = cv.getContext('2d').getImageData(0, 0, 60, 60).data;
            for (let i = 0; i < d.length; i += 4)
                if (d[i] > 200 && d[i + 1] < 60 && d[i + 2] > 200) return true;
            return false; }""")
        r.igual(hay_marca, False,
                "lo que vive en el lienzo de encima —la mira, los agarres, la "
                "goma— no se copia")

        # Y la marca SÍ estaba ahí: si no, la comprobación de arriba pasaría
        # por no haber nada que encontrar.
        seguia = pagina.evaluate("""async () => {
            pintar();
            await new Promise(r => requestAnimationFrame(() => r()));
            const e = encima.getContext('2d');
            e.save(); e.setTransform(1, 0, 0, 1, 0, 0);
            e.fillStyle = 'rgb(255,0,255)';
            e.fillRect(0, 0, 60, 60);
            e.restore();
            const d = e.getImageData(0, 0, 60, 60).data;
            return d[0] > 200 && d[1] < 60 && d[2] > 200; }""")
        r.igual(seguia, True,
                "(control: la marca estaba puesta cuando se armó la imagen)")

        r.igual(pagina.errores, [], "y no hubo un solo error de JavaScript")
