"""La versión de draw101  ·  un solo lugar.

Hasta el 31-ago-2026 el número vivía escrito a mano en `build/armar_paquete.py`
y nadie lo subía: ocho instaladores distintos salieron llamándose todos
`DIBUJADOR-0.9.0-setup.exe`. Desde dentro de la app no había manera de saber
cuál estaba corriendo. Eso se acabó aquí:

  · el número se declara **una vez**, en este archivo;
  · `build/armar_paquete.py` lo lee de aquí para el `.nsi` y para el nombre
    del `.exe`;
  · la app lo enseña en el pie y el comando `VERSION` cuenta qué cambió;
  · el armador se niega a repetir versión si el código cambió (ver
    `build/entregas.json`).

Numeración: `mayor.menor.parche`.
  · **parche** — se arregló algo, nada nuevo que aprender.
  · **menor** — hay función nueva o cambió cómo se comporta algo.
  · **mayor** — 1.0.0 el día que el taller dibuje un plano completo aquí sin
    volver a AutoCAD.
"""

from __future__ import annotations

VERSION = "0.21.0"
FECHA = "2026-09-19"

# Qué trae cada entrega, en el idioma del taller y no en el del código.
# La más nueva arriba. Lo que se lista aquí es lo que el comando VERSION
# enseña en la consola.
BITACORA: list[dict] = [
    {
        "version": "0.21.0",
        "fecha": "2026-09-19",
        "cambios": [
            "draw101 se abre entrando con tu cuenta de la suite 101: tu correo "
            "y contraseña, o tu cuenta de Google. Ya no hace falta teclear una "
            "clave, porque la licencia va ligada a tu correo.",
            "La clave T101-… sigue funcionando, abajo en la misma pantalla, "
            "para una máquina de taller sin internet estable o para una "
            "licencia que ya te habían entregado.",
            "Sin internet la app abre igual mientras tu licencia no haya "
            "vencido. Cuando vence y no hay forma de preguntarle a la suite, "
            "no abre y te lo dice con esas palabras: nunca se queda a medias.",
            "Cada equipo cuenta como un lugar de tu licencia. Los lugares se "
            "ven y se liberan desde master101.",
        ],
    },
    {
        "version": "0.20.6",
        "fecha": "2026-09-15",
        "cambios": [
            "Cambiar de unidades (UNIDADES) ya es un paso del historial: Ctrl+Z "
            "lo deshace y devuelve tamaños y unidad, y los siguientes Ctrl+Z "
            "siguen en orden. Antes el cambio no se anotaba, y deshacer después "
            "de escalar restauraba la acción anterior con los números de antes "
            "(en milímetros dentro de un plano en centímetros): lo dibujado "
            "«desaparecía» diez veces más lejos.",
            "El aviso de versión nueva tiene respaldo: si el motor no llega al "
            "sitio de Taller 101, la interfaz consulta con el motor de red del "
            "navegador (los mismos certificados y proxy que Chrome) y también "
            "baja el instalador por ahí; se comprueba la huella igual. Y cuando "
            "no se pudo consultar, el cuadro dice la razón exacta.",
            "Pruebas t021 (unidades y deshacer, 20 comprobaciones) y t022 "
            "(actualizador: razón del fallo y respaldo, 17 comprobaciones).",
        ],
    },
    {
        "version": "0.20.5",
        "fecha": "2026-09-15",
        "cambios": [
            "Seguridad del botón «Instalar ODA»: el instalador del convertidor "
            "sólo se baja de opendesign.com por https. El puntero de Taller 101 "
            "puede decir qué versión, pero ya no de dónde: una liga ajena se "
            "ignora. Antes se corría la liga que dijera el puntero, tal cual.",
            "Si el puntero declara la huella sha256 del instalador, se comprueba "
            "antes de correr msiexec; si no cuadra, se borra y no se instala.",
            "Prueba t020 (ODA: dominio y huella, 28 comprobaciones). Sin cambios "
            "en el dibujo.",
        ],
    },
    {
        "version": "0.20.4",
        "fecha": "2026-09-13",
        "cambios": [
            "RECORTAR sobre polilíneas. Se quita sólo el trozo entre los dos "
            "cruces que rodean el clic y lo que queda sigue siendo polilínea: "
            "en un extremo se acorta, en medio quedan dos, una cerrada se abre "
            "por ahí. Los tramos curvos se cortan como arcos exactos.",
            "Arreglo del índice de selección: tras recargar el dibujo entero "
            "sin picar nada en medio, la primera edición dejaba el índice del "
            "plano anterior (entidades borradas seguían «vivas» al clic y las "
            "nuevas no se dejaban picar).",
            "Fluidez: los círculos y arcos viajan con tantos segmentos como pida "
            "su radio (un barreno de ⌀5 con 16 puntos, no 73); en planos con "
            "muchos barrenos baja lo que se pinta.",
            "PERF anota las llamadas al motor que tardaron más de 150 ms o que "
            "obligaron a recargar todo (ruta, tiempo, peso), junto a los cuadros "
            "lentos: al reportar «se puso lento» ya se ve qué fue.",
            "Prueba t019 (RECORTAR en polilínea, 19 comprobaciones) y plano "
            "sintético de 21 700 entidades para medir (pruebas/carga/).",
        ],
    },
    {
        "version": "0.20.3",
        "fecha": "2026-09-12",
        "cambios": [
            "El valor tecleado manda sobre el snap. Una LÍNEA de «200» mide 200 "
            "aunque el ratón agarre un endpoint a 150 en el camino; el snap sólo "
            "da la dirección. En RECTÁNGULO, con la X tecleada, el snap ya no "
            "borra el valor: aporta la Y y la X sigue siendo la tecleada. Igual "
            "con ORTHO: el snap se proyecta al eje.",
            "ESCALARD (ESD, SCD): escala en UNA sola dirección. Base → referencia "
            "marca el eje y lo que mide hoy; el punto nuevo (o el factor) dice lo "
            "que debe medir sobre ese eje. Lo perpendicular no se toca: un mueble "
            "de 900 de ancho pasa a 1000 sin cambiar el alto. Los círculos se "
            "vuelven la elipse exacta; los arcos sueltos no se escalan y se avisa.",
            "Pruebas t017 (tecleado vs. snap, 11 comprobaciones) y t018 "
            "(ESCALARD, 13 comprobaciones). Se comprobó que en COPIAR el espacio "
            "ya confirma el valor como Enter, en la cajita y en la línea de "
            "comandos (venía de X.0.2).",
        ],
    },
    {
        "version": "0.20.2",
        "fecha": "2026-09-12",
        "cambios": [
            "Medidas negativas: «-300» en el ancho o el alto de un RECTÁNGULO "
            "(en la cajita X/Y o en la línea de comandos) dibuja hacia la "
            "izquierda o hacia abajo, esté donde esté el ratón. Sin signo, "
            "como siempre: el tamaño lo pone el número y la dirección el cursor. "
            "Vale igual para la longitud de LÍNEA y demás comandos con medida "
            "fija: «-200» va al lado contrario del cursor.",
            "El campo ya fijado de la cajita muestra lo tecleado con su signo "
            "(«-300»), y ese valor manda al rematar con Enter.",
            "Todo lo de X.0.2 (pruebas t001–t015 y el arreglo de la cota al "
            "ESTIRAR) más la prueba t016 de medidas negativas: 17 "
            "comprobaciones tecleando de verdad en el navegador.",
        ],
    },
    {
        "version": "X.0.2",
        "fecha": "2026-09-10",
        "cambios": [
            "Vuelven las pruebas: `pruebas/t001` a `t015` y `verificar.py`, "
            "341 comprobaciones. Las cuatro de interfaz manejan el programa "
            "con un navegador de verdad; las de DWG fabrican el archivo con un "
            "motor y lo leen con el otro.",
            "ARREGLADO: al ESTIRAR una pieza acotada por un extremo, la línea "
            "de cota se iba de lado siguiendo un traslado que nunca ocurrió. "
            "Sólo se apuntaba el desplazamiento de los puntos que cambiaban, "
            "así que un estirado quedaba con un solo desplazamiento en la "
            "lista y «todos iguales» se cumplía sola. Lo cazó t008.",
        ],
    },
    {
        "version": "X.0.1",
        "fecha": "2026-09-10",
        "cambios": [
            "La línea X es la de PRUEBAS de la reconstrucción: mismo código que "
            "la 0.20.1, armado de nuevo desde cero para comprobar que el "
            "proyecto se puede volver a compilar completo. Lo que cambie de "
            "aquí en adelante se numera X.0.2, X.0.3…",
            "El código fuente se recuperó del propio instalador 0.20.1 "
            "(motor Python, interfaz, motores de DWG, runtime empotrado) y "
            "vuelve a vivir en la carpeta t101d, no dentro de un chat.",
            "Una entrega de la línea X no busca actualizaciones ni avisa de "
            "versión nueva: se instala a mano, que es lo que se está probando "
            "(core/actualizar.py, es_de_pruebas).",
        ],
    },
    {
        "version": "0.20.1",
        "fecha": "2026-09-09",
        "cambios": [
            "ARREGLADO: el aviso de versión nueva tardaba o no salía. El motor "
            "consulta el sitio en un hilo desde que arranca (a los 2 s, con "
            "reintentos cada 3 min si no hay red, luego cada 6 h) y la "
            "interfaz ya no espera a la red; se avisa a los 3 s de abrir.",
            "El aviso de versión nueva es un letrero arriba del lienzo con "
            "«Actualizar» y «Después», no sólo una línea en la consola.",
            "Al correr el dibujo dentro de una ventana de la hoja (EDITARVENTANA, "
            "arrastrando el interior) se ve en vivo cómo queda: la hoja se "
            "pinta corrida con el ratón y recortada al marco, no a ciegas.",
            "Los dibujos nuevos nacen en centímetros. La altura de texto por "
            "omisión (7.5 mm) y el paso de la rejilla se expresan en las "
            "unidades del dibujo.",
            "ARREGLADO: al jalar un grip con la rejilla encendida, el paso se "
            "tomaba en unidades del dibujo en vez de en mm (en cm saltaba de "
            "10 en 10 cm).",
        ],
    },
    {
        "version": "0.20.0",
        "fecha": "2026-09-09",
        "cambios": [
            "ESCALAR como en cualquier CAD: punto base, punto de referencia y "
            "punto nuevo (o se teclea el factor en cualquiera de los dos pasos).",
            "Selección por cruce con geometría real: entra sólo lo que la ventana "
            "toca de verdad, no lo que cae en la caja envolvente.",
            "Cajita junto al cursor para cualquier dato que pida una herramienta "
            "(distancia, radio, factor…), no sólo para puntos.",
            "Cuadro de selección junto al cursor más fino: 6 px y raya de 1 px.",
            "Las propiedades de la capa ya no van fijas en el panel: clic derecho "
            "sobre la capa.",
            "VENTANAHOJA (VH): se recuadra una zona del modelo y se crea una hoja "
            "cuya ventana enseña justo eso.",
            "RECTANGULO: dos caminos y ninguno más — clic en las dos esquinas, o "
            "ancho Enter alto Enter (también en la línea de comandos).",
            "Referencia nueva «Proyección perpendicular»: seguir la perpendicular "
            "desde el punto anterior aunque se salga del trazo, y donde cruza con "
            "otro. Con línea de rastreo punteada.",
            "Un solo texto, de párrafo: Enter guarda, Alt+Enter hace renglón nuevo. "
            "Con justificación izquierda/centro/derecha respecto al origen "
            "(también en propiedades). Al DXF sale como MTEXT si lleva renglones.",
            "Menú radial: Editar y Cuadrado intercambiados; sale al mover 2 px con "
            "el botón derecho apretado.",
            "Grips en los puntos medios de líneas y polilíneas: jalarlo traslada el "
            "tramo entero; los tramos vecinos siguen conectados.",
            "Cota recta: el tercer punto decide si mide en X o en Y (como DIMLINEAR).",
            "Panel «Cotas del documento» a la derecha (texto y flechas de un jalón); "
            "por cota, tamaño propio y opción de encadenar al base del documento.",
            "Cada hoja tiene su propio tamaño de cota (mm en papel), en el cuadro de "
            "la hoja; el modelo no cambia.",
            "RAYADO: galería de patrones junto al cursor con previa en el modelo "
            "(Enter confirma). Los patrones se dibujan de verdad en pantalla, PDF y "
            "SVG: ANSI31, ANSI32, ANSI37, cuadrícula, puntos, ladrillo, concreto…",
            "Selección previa: con algo seleccionado, el comando aplica a eso sin "
            "volver a pedirlo (también en desfase, recortar, rayado…).",
            "Un parpadeo casi imperceptible del lienzo cuando un comando cambió "
            "algo; si no cambió nada, nada (se apaga en Configuración).",
            "Al colocar la línea de cota hay referencias a las líneas de cota de "
            "otras cotas: una fila de cotas cae en el mismo renglón.",
            "Clic derecho corto sobre una entidad: sus propiedades ahí mismo, "
            "editables en vivo; se cierra con clic fuera o Esc.",
            "Ventanas de la hoja con el ratón (EDITARVENTANA / VP, botón en la "
            "barra): esquinas y lados cambian el tamaño, el marco la mueve, el "
            "interior corre el dibujo. VENTANANUEVA (NV) agrega ventanas; "
            "BORRARVENTANA (BV) las quita. Al cambiar el tamaño del papel, la "
            "única ventana vuelve a ocupar toda el área útil.",
            "La escala del pie de plano y del cuadro de la hoja se elige de una "
            "lista de escalas (1:1 … 1:200) más «Otra…», sin teclear los «:».",
            "ARREGLADO: Extents se iba a kilómetros en planos con bloques "
            "anidados girados (la caja de una inserción no giraba ni resolvía "
            "los sub-bloques) y ya no se podía volver.",
            "ARREGLADO: la búsqueda de referencias congelaba la ventana en un "
            "plano de una sola línea horizontal.",
        ],
    },
    {
        "version": "0.19.4",
        "fecha": "2026-09-08",
        "cambios": [
            "ARREGLADO: al instalar una actualización desde el programa, Windows "
            "decía «No se ha encontrado la ruta de acceso de la red» y el "
            "instalador no arrancaba (las comillas de la orden llegaban "
            "escapadas). Ahora el instalador se abre por un .bat de tres "
            "renglones, sin ventana negra.",
        ],
    },
    {
        "version": "0.19.3",
        "fecha": "2026-09-08",
        "cambios": [
            "Cada herramienta lleva su icono junto al cursor (tijera en "
            "RECORTAR, flecha en EXTENDER, cuatro flechas en MOVER…) con la "
            "caja de selección bien marcada en azul.",
            "Las cotas y directrices ya se mueven, copian, giran y escalan. "
            "Una cota pegada a una pieza sigue a la pieza entera; moverla sola "
            "sólo acerca o aleja la línea de cota. Sus puntos son grips.",
            "Cada pregunta numérica recuerda su última respuesta (desfase, "
            "empalme, escala…) y la ofrece por omisión; Enter o espacio la toman.",
            "El espacio confirma al teclear números (línea de comando, entrada "
            "dinámica y cuadros); en texto libre sigue siendo espacio.",
            "Texto: altura por omisión 7.5 mm (antes 2.5), y recuerda la última.",
            "Tipo de línea y escala del tipo por entidad, en el panel de "
            "propiedades.",
            "RECTANGULO: la cajita dinámica pide X y Y (ancho y alto); Tab o "
            "Enter pasan de X a Y.",
            "UNIDADES (Ayuda ▾ → Unidades del dibujo, y en el cuadro de la "
            "hoja): mm, cm o m; escala lo dibujado para conservar el tamaño "
            "real; el DXF sale con la unidad declarada.",
            "La escala escrita en la hoja manda: «1:50» en el pie o en el "
            "cuadro pone la ventana a esa escala.",
            "CENTRAR: centra el dibujo en la ventana de la hoja (Enter: todo; "
            "clic: ese punto al centro); botón «Centrar el dibujo» en el cuadro "
            "de la hoja.",
            "Ayuda ▾ → Guía de herramientas (PDF): icono, nombre y qué hace "
            "cada herramienta, en español o inglés (GUIA).",
        ],
    },
    {
        "version": "0.19.2",
        "fecha": "2026-09-07",
        "cambios": [
            "draw101 se actualiza solo: al arrancar (y una vez al día) revisa "
            "en el sitio de Taller 101 si hay versión nueva; Ayuda ▾ → Buscar "
            "actualizaciones (o ACTUALIZAR) la baja, la comprueba con su huella "
            "sha256 y corre el instalador cuando tú digas. Se puede ignorar una "
            "versión o apagar la revisión automática.",
            "Avisos de Taller 101 dentro del programa: Ayuda ▾ → Avisos (o "
            "AVISOS). Los nuevos marcan el menú con un punto; los importantes "
            "salen solos al arrancar. Lo leído no se repite.",
            "Ayuda ▾ → Licencias de terceros (LICENCIAS): cada componente ajeno "
            "que viaja dentro del programa, con su versión, licencia y texto.",
            "El PDF de fondo (PDFFONDO) se lee ahora con pypdfium2 en vez de "
            "PyMuPDF: misma función, licencia BSD/Apache en vez de AGPL. Los "
            "caminos que vuelven a su origen (círculos) entran cerrados.",
        ],
    },
    {
        "version": "0.19.1",
        "fecha": "2026-09-07",
        "cambios": [
            "La cota se ve como va a quedar mientras se coloca: líneas de "
            "extensión, línea de cota, palomitas y la cifra real siguen al "
            "ratón, en vez de dos rayas punteadas. COTA, COTAH, COTAV, "
            "COTAALINEADA (con la cifra girada) y las cadenas continua y de "
            "línea base.",
            "Rendimiento con la goma del ratón (segundo punto de LINEA, cota): "
            "el pintado ya no consulta los estilos de la página en cada cuadro, "
            "la cajita de entrada dinámica se mide una sola vez y se mueve sin "
            "reacomodar la pantalla, y la búsqueda de intersecciones del osnap "
            "se limita a las 60 piezas más cercanas.",
            "Comando DIAG ON/OFF: anota los cuadros que tarden más de 40 ms "
            "(pintado) o 25 ms (ratón) con su desglose; PERF los enseña. Sirve "
            "para reportar la lentitud con datos.",
        ],
    },
    {
        "version": "0.19.0",
        "fecha": "2026-09-06",
        "cambios": [
            "El programa se llama **draw101**. Mismo logotipo de Taller 101 con "
            "«draw» en vez de «taller»; el instalador quita t101draw y la "
            "carpeta de usuario se hereda sola.",
            "Inglés de fábrica. Español en Ayuda ▾ → Configuración (o IDIOMA "
            "ES). Los comandos se aceptan en los dos idiomas siempre: LINE y "
            "LINEA, MOVE y MOVER…; AYUDA/HELP los lista en el idioma elegido.",
            "Pie de plano nuevo: una barra vertical pegada al marco derecho, "
            "como en los despachos de arquitectura (logotipo, proyecto, "
            "cliente, dibujo, dibujó; abajo escala, fecha, folio y revisión). "
            "La ventana de la hoja aprovecha todo el alto.",
            "Doble clic sobre un dato del pie, en la hoja, lo edita ahí mismo: "
            "sólo el texto; Enter guarda, Esc cancela, vacío = automático. Es "
            "el mismo dato que enseña el cuadro PLANO.",
            "Imprimir: se elige el tamaño de papel y la hoja sale **centrada "
            "en el papel**, no en los márgenes de la impresora; si no cabe se "
            "reduce a escala. Botón «Vista previa» (y comando VISTAPREVIA) que "
            "enseña el papel con la hoja puesta y el borde que la impresora no "
            "alcanza.",
            "ARREGLADO: teclear la longitud durante LINEA y hacer clic la "
            "ignoraba (sólo Enter servía). Ahora el clic la toma, y mientras se "
            "teclea se ve la previa: el rayo de dirección punteado y, encima, "
            "el tramo exacto de esa medida con su cifra.",
        ],
    },
    {
        "version": "0.18.2",
        "fecha": "2026-09-06",
        "cambios": [
            "Los números —coordenadas, pie, panel, cotas, textos del plano y "
            "PDF— van en Fira Sans; el texto sigue en Raleway. Raleway trae "
            "cifras «old style» que cuelgan y suben, y una medida no se leía. "
            "Sólo cambian los dígitos y los signos de medida (° ⌀ ± × %), y "
            "van del mismo ancho para que no bailen.",
            "ARREGLADO: un DWG de 60 MB (A8-501) abría vacío con «estado.trazos "
            "is not iterable». Dos causas: el conversor de DWG se quedaba sin "
            "memoria (ahora se le da hasta el 70 % de la RAM), y el plano "
            "traía 664 plantas de 50 000 vértices cada una que, explotadas, "
            "eran 559 MB que el navegador no podía ni leer.",
            "Bloques pesados como los hace AutoCAD: la definición viaja una "
            "vez y cada inserción es un punto, una escala y un giro. De cerca "
            "se pintan con todo el detalle; de lejos, como imagen; y con tres "
            "niveles de detalle en medio. Se piden solos conforme hacen "
            "falta; mientras llegan se ve su caja punteada. Los bloques "
            "chicos siguen como siempre.",
            "Si el motor contesta algo que el navegador no puede leer, ahora "
            "lo dice con claridad en vez de dejar el plano vacío.",
        ],
    },
    {
        "version": "0.18.1",
        "fecha": "2026-09-06",
        "cambios": [
            "Lo que decía el PERF de Mike: pintar cuesta 34 ms, pero cada "
            "operación tardaba medio segundo aunque moviera una sola línea. "
            "El motor recalculaba la caja de las 15 000 entidades dos veces "
            "por operación (250 ms cada una). Ahora la guarda y sólo rehace "
            "la de lo que se tocó: mover una línea, 500 ms → 20 ms.",
            "El historial copiaba cada entidad con deepcopy: 2 000 entidades, "
            "medio segundo. Copia a mano, cinco veces más rápido.",
            "El recolector de basura de Python paraba todo 300 ms cada tantos "
            "objetos nuevos en un plano grande; se le suben los umbrales y lo "
            "cargado se congela.",
            "El índice de selección se parcha con lo que cambió en vez de "
            "rearmarse entero (180 ms por operación en un plano de medio "
            "millón de primitivas).",
            "Con mucho seleccionado (un grupo de 1 200 partes) el resaltado se "
            "volvía a trazar en cada movimiento del ratón. Ahora se pinta una "
            "vez como imagen y se copia; al panear se corre con el plano. "
            "Cuesta lo mismo con una entidad que con diez mil.",
            "Al acercarse con la rueda, la foto se ve borrosa hasta el regen "
            "(como AutoCAD) en vez de pixelada en bloques.",
        ],
    },
    {
        "version": "0.18.0",
        "fecha": "2026-09-06",
        "cambios": [
            "Navegar ya no redibuja el plano: mientras se arrastra la vista o "
            "se gira la rueda se mueve una foto del plano (como la lista de "
            "despliegue de AutoCAD) y al detenerse el ratón se redibuja fino "
            "solo. En un plano pesado y alejado, cada movimiento costaba lo "
            "que pintar decenas de miles de trazos; ahora cuesta un milisegundo.",
            "REGEN (RE): redibuja fino y rehace el índice, como en AutoCAD. "
            "REGENERAR (REGENALL) además vuelve a pedir el dibujo al motor.",
            "RENDIMIENTO (PERF): mide en esta máquina cuánto cuesta pintar, "
            "navegar y seleccionar, y lo copia al portapapeles para reportarlo.",
            "Alejado del todo, las entidades que caben en un píxel se pintan "
            "como un píxel, una sola vez por píxel: 38 000 manchas se vuelven "
            "unos miles.",
            "La caja de selección es de 3 píxeles (PICKBOX de AutoCAD), con una "
            "segunda pasada de 6 sólo si no hubo nada. Antes eran 11 y 26: "
            "alejado, un clic en el vacío agarraba cosas a medio cuarto.",
            "ARREGLADO: mover o copiar miles de entidades en un plano grande "
            "se quedaba un segundo entero después de que el motor contestaba "
            "(88 millones de comparaciones para saber qué se borró).",
            "ARREGLADO: «hay un documento que no se guardó, ¿recuperarlo?» en "
            "cada arranque. Ahora sólo se ofrece si la vez pasada el programa "
            "no se cerró por la X (se cayó, lo mataron, se fue la luz). Cerrar "
            "por la X pregunta si guardar y, diga sí o no, no deja nada que "
            "recuperar. Decir que no a una copia tira todas las de ese dibujo. "
            "Lo recuperado abre como el archivo original, no como una copia "
            "dentro de la carpeta de autoguardado.",
            "Al cerrar con varias pestañas con cambios se avisa de todas, y "
            "«Guardar y salir» las guarda una por una.",
            "La consola de abajo mide dos renglones. El botoncito de la esquina "
            "—o F2, como la ventana de texto de AutoCAD— la abre a diez, con "
            "scroll, para repasar lo que pasó.",
            "Clic derecho en un botón de la barra: las otras formas de esa "
            "herramienta, como el flyout de AutoCAD. Círculo: centro-radio, "
            "centro-diámetro, 2 puntos, 3 puntos. Arco: 3 puntos, "
            "centro-inicio-fin, inicio-fin-radio, inicio-centro-ángulo. "
            "Rectángulo: esquinas, por el centro, por medidas, 3 puntos "
            "(girado). Polilínea: polígono regular (POLIGONO). Elipse: por los "
            "extremos del eje. Spline: por puntos de control (Bézier, curva "
            "orgánica, dibujada como B-spline de verdad). Línea: desde el punto "
            "medio. Texto: de párrafo. Cota: alineada, encadenada, desde base. "
            "Copiar: arreglo. Todas se teclean también (C 3P, A CIF, REC C…).",
            "La barra: el bloque COTAS se llama ANOTACIONES y trae el Texto; "
            "el texto de párrafo va en el clic derecho de Texto.",
            "BORRADOR (DRAFT): modo borrador como el de LibreCAD y QCAD. "
            "Líneas de 1 px, sin patrones, textos como cajas. Para navegar un "
            "plano pesado en una máquina floja; se apaga con BORRADOR OFF.",
        ],
    },
    {
        "version": "0.17.1",
        "fecha": "2026-09-06",
        "cambios": [
            "El ODA File Converter se instala desde el programa: comando ODA, "
            "o clic en el indicador «DWG» del pie. Lo baja de opendesign.com "
            "y corre su instalador (se acepta su licencia y el permiso de "
            "Windows). Es gratuito y convierte DWG 2 o 3 veces más rápido y "
            "con más fidelidad que el motor propio.",
            "La versión que se baja la dice un link fijo de Taller 101 "
            "(t101draw.netlify.app/oda.json), no la página de ODA: cuando ODA "
            "saque versión nueva se cambia ahí y todos los t101draw la ven. "
            "Si ese link no contesta, se lee la página de ODA; si tampoco, "
            "se abre la página para bajarlo a mano.",
            "Al abrir un DWG de más de 5 MB sin ODA, se ofrece instalarlo. "
            "Una sola vez.",
        ],
    },
    {
        "version": "0.17.0",
        "fecha": "2026-09-05",
        "cambios": [
            "El programa se llama t101draw (así, en minúscula). Se instala en "
            "Taller 101\\t101draw y quita solo la versión DIBUJADOR anterior; "
            "las preferencias, los bloques y el autoguardado se copian a la "
            "carpeta nueva la primera vez que abre.",
            "Pantalla de carga: un plano de cocina en perspectiva flotando "
            "sobre el escritorio —sin recuadro— con la marca en medio, mientras "
            "arranca el motor.",
            "Menú radial tipo Maya: clic derecho **sostenido** y mover el "
            "ratón. Línea, Círculo, Cuadrado, Texto, Cotas ▸, Trimear, Mover y "
            "Editar ▸ (Espejear, Rotar, Copiar, Escalar, Borrar). Las cotas "
            "están a las seis y la recta en medio: derecho, abajo, más abajo, "
            "soltar. Manda el ángulo, no hay que atinarle.",
            "Clic derecho corto = Enter, como en AutoCAD. Mover la vista: botón "
            "central, o Espacio + arrastrar con el izquierdo (laptop).",
            "Shift + clic suma a la selección; no choca con Shift como ortho "
            "momentáneo. Alt + clic toma un solo miembro de un grupo. Ctrl "
            "queda libre.",
            "La barra de herramientas va por bloques de dos renglones con su "
            "título: TRAZO, COTAS, TEXTO, MODIFICAR, BLOQUES, HOJA.",
            "ARREGLADO: al picar donde había cinco o seis cosas encimadas "
            "salían varios menús de «cuál» y sólo se cerraba el último. Ahora "
            "hay uno solo aunque se pique tres veces seguidas.",
        ],
    },
    {
        "version": "0.16.1",
        "fecha": "2026-09-04",
        "cambios": [
            "ARREGLADO: al agrandar la ventana, la consola y el pie se salían "
            "por abajo. El lienzo contaba su tamaño en píxeles de pantalla "
            "(× la escala de Windows) como contenido mínimo de su caja, y cada "
            "ajuste lo agrandaba más. Ahora el lienzo va absoluto: el tamaño lo "
            "pone la caja, nunca al revés.",
            "La interfaz ya no se agranda con Ctrl+rueda ni Ctrl+más: en un "
            "CAD Ctrl está apretado la mitad del tiempo, y un giro de rueda "
            "sobre el panel dejaba toda la ventana al 125 %. El zoom de "
            "página queda clavado en 1.",
            "El lienzo se ajusta con lo que cambia de tamaño su caja (panel, "
            "barra, monitor), no sólo la ventana.",
        ],
    },
    {
        "version": "0.16.0",
        "fecha": "2026-09-04",
        "cambios": [
            "El ratón va suelto en planos pesados: las referencias a objeto se "
            "buscaban recorriendo el plano entero en cada movimiento (9 a 16 ms "
            "por cuadro en el de Mondelez); ahora van por el índice y sólo "
            "cuando se está pidiendo un punto (0.1 ms).",
            "Seleccionar mucho ya no traba: con 5 000 entidades cada cuadro "
            "costaba 1.5 segundos por los grips. Tope de 100 como el "
            "GRIPOBJLIMIT de AutoCAD, y no se pinta lo que no está en pantalla: "
            "12 ms.",
            "El panel de propiedades pedía las entidades una por una (5 000 "
            "peticiones); ahora una.",
            "Traer el dibujo al navegador: 23 s → 2 s (serialización con orjson).",
            "Reabrir un plano que no cambió: 60 s → 2 s (caché de apertura).",
            "Indicador de «trabajando» cuando algo pasa de medio segundo, con "
            "qué se está haciendo: «Convirtiendo el DWG (21 MB)…».",
            "GRUPO (Ctrl+G) y DESAGRUPAR (Ctrl+Shift+G): picar uno pica todos. "
            "Ctrl+Shift+clic pica uno solo.",
            "EXPLOTAR (X): bloques, polilíneas, rayados, cotas y entidades "
            "ajenas, en sus partes. Es lo que vuelve editable lo que vino de "
            "otro programa.",
        ],
    },
    {
        "version": "0.15.0",
        "fecha": "2026-09-04",
        "cambios": [
            "ARREGLADO: faltaban los rótulos de los bloques con atributos. En "
            "el DWG de Mondelez eran 1 316 etiquetas —las CA-23 de cada "
            "mueble— que se leían y no se pintaban. Ahora se ven, y son texto "
            "suelto: se pican y se corrigen.",
            "Las referencias externas (XREF) se van a buscar y se montan. El "
            "fondo de arquitectura de un plano suele ser eso, y antes sólo se "
            "decía que faltaba.",
            "Se busca donde el plano dice, y también al lado del plano — que "
            "es como llegan los archivos por correo.",
            "Si no está, se dice cuál falta y qué archivo hay que conseguir.",
            "ARREGLADO: la letra dentro de un bloque escalado no escalaba: el "
            "rótulo se salía de su cuadro.",
        ],
    },
    {
        "version": "0.14.0",
        "fecha": "2026-09-04",
        "cambios": [
            "ARREGLADO: dibujar estando en una hoja creaba la entidad en el "
            "MODELO, con coordenadas de papel. Se trazaba y no aparecía en "
            "ninguna parte. Ahora modelo y hoja son dos espacios de verdad.",
            "Lo que se dibuja sobre una hoja es de esa hoja: se ve, se "
            "selecciona, se mueve y se borra ahí, y no se cuela al modelo.",
            "Acotando sobre la hoja, la referencia a objeto se engancha a lo "
            "que se ve por la ventana.",
            "Y la cota anuncia la medida del mueble, no la del papel: sobre "
            "una ventana a 1:20, 172 mm de papel se acotan como 3 440.",
            "El texto de una cota de papel sale a tamaño de papel (2.5 mm), no "
            "con el factor de escala del modelo.",
            "Dos hojas no pueden llamarse igual. Renombrar una se lleva lo "
            "dibujado en ella; borrarla, también.",
            "Al exportar DXF, lo de cada hoja va a su hoja y no al modelo.",
        ],
    },
    {
        "version": "0.13.1",
        "fecha": "2026-09-04",
        "cambios": [
            "ARREGLADO: TEXTO no dejaba escribir. Preguntaba primero la altura "
            "y rechazaba las letras sin decir que la pregunta era otra. Ahora "
            "sale un cuadro con el texto, la altura y la rotación juntos.",
            "Doble clic encima de un texto lo abre para corregirlo, sin tener "
            "que borrarlo y volver a ponerlo.",
            "Al trazar, teclear la medida ya no dibuja de un jalón hacia donde "
            "esté el ratón: la medida se fija y el clic elige la dirección. "
            "Enter también sirve, con la dirección de ese momento.",
            "Shift invierte el ortho mientras se tiene apretado, en los dos "
            "sentidos, y el pie lo enseña.",
            "Mover la vista es con el botón central o el derecho. Shift ya no, "
            "porque ahora es el ortho.",
        ],
    },
    {
        "version": "0.13.0",
        "fecha": "2026-09-04",
        "cambios": [
            "Los planos del archivo ajeno se abren como hojas: al abrir el DWG "
            "de Mondelez salen sus 40 planos en las pestañas, con sus 215 "
            "ventanas, cada una encuadrada y a su escala.",
            "Cada hoja importada trae SU marco y SU pie de plano, no el "
            "nuestro encima.",
            "Se respetan las capas congeladas por ventana.",
            "ARREGLADO: los bloques anónimos del archivo se tiraban. En el DWG "
            "de Mondelez eran 43 inserciones que no se dibujaban — pedazos de "
            "plano que faltaban sin avisar.",
            "ARREGLADO: los rótulos salían con los códigos del archivo "
            "(«{\\fRomanS_|V50…;PLANTA}» en vez de «PLANTA»).",
            "Si el plano usa referencias externas que no vienen en el archivo, "
            "se dice al abrir en vez de dejar el hueco callado.",
            "Abrir un plano grande cuesta 8 segundos menos y 350 MB menos de "
            "memoria: el archivo original se guarda en disco, no en memoria.",
            "Armar una hoja con varias ventanas es unas seis veces más rápido.",
        ],
    },
    {
        "version": "0.12.1",
        "fecha": "2026-09-02",
        "cambios": [
            "Con algo seleccionado, el ratón vuelve a ir suelto: se buscaba "
            "recorriendo el plano entero en cada movimiento.",
            "Picar en un plano grande es unas veinte veces más rápido.",
            "Menú para elegir cuando un clic cae encima de varias cosas; al "
            "pasar por cada renglón se enciende esa entidad en el dibujo.",
            "Sumar a la selección es con Ctrl. Con Shift nunca funcionó: "
            "Shift+arrastrar es mover la vista.",
        ],
    },
    {
        "version": "0.12.0",
        "fecha": "2026-09-02",
        "cambios": [
            "Mover el ratón sobre un plano grande ya no lo redibuja: la mira y "
            "la selección viven en su propio lienzo encima.",
            "Sólo se dibuja lo que cabe en la pantalla; acercarse a un detalle "
            "deja de costar lo que mide el plano entero.",
            "Se pinta por lotes de color en vez de trazo por trazo.",
            "Los repintados se juntan en un cuadro: el ratón ya no encola "
            "trabajo más rápido de lo que se puede pintar.",
        ],
    },
    {
        "version": "0.11.2",
        "fecha": "2026-09-02",
        "cambios": [
            "DIBUJADOR ya sale en «Abrir con» de un DWG y de un DXF, y en "
            "Configuración → Aplicaciones predeterminadas.",
            "No se roba la asociación: quién abre los DWG por omisión lo "
            "sigue decidiendo el usuario.",
        ],
    },
    {
        "version": "0.11.1",
        "fecha": "2026-09-01",
        "cambios": [
            "ARREGLADO: la barra flotante tapaba el tercio de arriba del "
            "plano y se comía los clics — no se podía dibujar ahí.",
            "Por donde la barra flotante no tiene botón, el clic pasa al plano.",
            "El rectángulo acepta medidas: primera esquina, M, ancho, alto.",
            "La fila de pestañas ya no se ve con un solo dibujo abierto.",
        ],
    },
    {
        "version": "0.11.0",
        "fecha": "2026-09-01",
        "cambios": [
            "Al jalar un extremo, ahora sí se engancha al de al lado.",
            "Cuadro con los ocho modos de referencia (F3): extremo, medio, "
            "centro, cuadrante, intersección, perpendicular, nodo y cercano.",
            "Las cotas nacen con texto y flechas de 30 mm en el dibujo.",
            "Las cotas se pueden picar por sus rayas y atrapar con una ventana.",
            "Más tolerancia al seleccionar: ya no hay que atinarle a la raya.",
            "La capa de trabajo se cambia con doble clic, no con uno.",
            "Fantasma translúcido al mover, copiar, rotar y espejear.",
            "La barra de herramientas, por secciones con su nombre.",
            "El panel de la derecha se ensancha arrastrando el borde.",
            "Guardar como.",
            "Hojas en carta, tabloide y a la medida, con cuadro de diálogo.",
            "Imprimir en impresora de verdad con Ctrl+P.",
            "Pantalla de inicio con los planos recientes.",
            "Pestañas: varios dibujos abiertos a la vez.",
            "Se pide la tarjeta de video discreta al arrancar.",
        ],
    },
    {
        "version": "0.10.0",
        "fecha": "2026-08-31",
        "cambios": [
            "Abre DWG sin instalar nada aparte (tres motores en cascada).",
            "Los planos ajenos se ven, se seleccionan y se borran.",
            "Dibujos en metros o pulgadas se convierten solos a milímetros.",
            "Comandos ~25 veces más rápidos: se repinta sólo lo que cambió.",
            "Dibujo nuevo con dos capas: 0 y COTAS.",
            "Las cotas se trazan siempre en la capa COTAS.",
            "Enter cierra el comando de línea.",
            "UNIR (J): varias líneas y arcos en una polilínea.",
            "Barra de herramientas flotante o anclable, en varias filas.",
            "El espacio confirma igual que Enter.",
            "La versión se ve en el pie y el comando VERSION cuenta el resto.",
        ],
    },
    {
        "version": "0.9.0",
        "fecha": "2026-08-28",
        "cambios": [
            "Primer instalador de Windows, sin dependencias que instalar.",
            "Dibujo, edición, cotas, bloques, hojas e impresión a PDF.",
            "Ocho compilaciones distintas salieron con este mismo número.",
        ],
    },
]


def bitacora(desde: str | None = None) -> list[dict]:
    """La bitácora, opcionalmente recortada a partir de una versión."""
    if desde is None:
        return BITACORA
    salida = []
    for e in BITACORA:
        salida.append(e)
        if e["version"] == desde:
            break
    return salida


def como_tupla(v: str = VERSION) -> tuple[int, int, int]:
    """`"0.10.0"` → `(0, 10, 0)`. Para comparar sin sorpresas alfabéticas:
    ordenado como texto, 0.9.0 sale *después* de 0.10.0."""
    partes = (v.split("-")[0].split(".") + ["0", "0", "0"])[:3]
    return tuple(int(p) if p.isdigit() else 0 for p in partes)  # type: ignore[return-value]
