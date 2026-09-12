<!-- Copiado tal cual del documento de Drive «draw101 handoff», el 12-sep-2026,
     con el conector de Google Drive. Sólo se le quitaron los escapes que Google
     mete al exportar a markdown (\- \+ \: y demás). No se corrigió el contenido:
     es el documento del chat que reconstruyó draw101, y vale como está. -->

> **Nota del 12-sep-2026, al meter esto al repositorio.** Dos cosas de este
> documento ya no aplican, y conviene saberlo antes de seguirlas al pie de la
> letra:
>
> - **Ya no hace falta ningún PAT.** Desde el 10-sep la GitHub App de Claude
>   está instalada en `mikebalcazar` y el proxy pone la credencial en una
>   sesión de Claude Code. Si te encuentras un token en un archivo, no lo uses:
>   avísale a Mike para que lo revoque. Lo manda `OPERAR.md` §1.
> - **El repositorio ya existe y ya tiene la fuente**: es éste, y lo que estás
>   leyendo llegó en el mismo trabajo. El «pendiente 1» de este documento está
>   cerrado.
>
> Todo lo demás —las mediciones, las decisiones y las trampas— sigue vigente.

# draw101 — handoff

*Para el chat que continúe draw101, con acceso a los repos. Escrito el 10-sep-2026, al cerrar la reconstrucción. Todo lo que hay aquí está comprobado en esta sesión; lo que no, se dice que no.*

## Qué es draw101

El CAD 2D de Taller 101 y una de las siete apps de suite101. Lee y escribe DXF y DWG, dibuja, acota, arma hojas con pie de plano, imprime, y trae cocinas de Taller 101 por `.t101x` para devolver un paquete a SUPERVISOR. Las 80 funcionalidades del plan están hechas.

Cómo está armado:

| Pieza | Qué es |
| --- | --- |
| Motor | Python 3.11 — ezdxf, reportlab, pillow, pypdfium2, numpy |
| Backend | FastAPI + uvicorn en 127.0.0.1; **el documento vive en el servidor**, no en el navegador |
| Interfaz | HTML/CSS/JS con canvas 2D, sin empaquetador |
| DWG | LibreDWG (WebAssembly) y acad-ts, corridos con el Node de Electron |
| Envoltura | Electron 33 (para el instalador NSIS) |

## Lo primero que hay que hacer: el repo

**No existe repo de draw101.** Está verificado leyendo los ocho repos de `github.com/mikebalcazar`: draw101 aparece sólo como metadatos de distribución dentro de `descargas`. El código de la app no está en GitHub, en ninguna parte.

Toda la reconstrucción vive hoy en la carpeta local `C:\Users\mikeb\OneDrive\Escritorio\t101d`, y eso es un parche, no una solución: esta reconstrucción existe justamente porque el código vivía en un chat. **Tarea 1 del nuevo chat: crear el repo `draw101` y subir `draw101-fuente-X.0.2.zip` descomprimido.**

Lo que va en `.gitignore`: `runtime/python/` (140 MB, se repone del instalador), `node_modules/` de la raíz (`npm install`), `dist/`. Lo que **sí** va, aunque sea `node_modules`: `dwgjs/node_modules/` — son los dos motores de DWG y no se bajan con la misma versión garantizada.

## Cómo se recuperó el código (por si vuelve a pasar)

El código lo tenía el chat anterior y se perdió con él. No hubo que reescribir nada: el instalador `draw101-0.20.1-setup.exe` **lleva el proyecto dentro, en claro** — es un NSIS con `resources\app\` sin asar (Python, JS, CSS, fuentes, licencias) y `resources\python\` con el intérprete empotrado. Se abre con 7-Zip y sale entero.

Lo único que no viajaba dentro del instalador eran las pruebas y el armador. Las pruebas **ya se volvieron a escribir**; el armador se reemplazó por la receta de electron-builder que está en `package.json`.

## La línea X y el estado actual

Las entregas de la reconstrucción se numeran **X.0.1, X.0.2, …** La línea `0.x` quedó cerrada en 0.20.1. La X marca lo que son: entregas de prueba de un proyecto rearmado, a verificar en Windows antes de volver a numerar en serio.

- **X.0.1** — armada por Claude desde la fuente recuperada. **Probada por Mike en Windows: instala, abre, y lee un DWG real. Nada se vio raro.**
- **X.0.2** — el código que está hoy en la carpeta: X.0.1 + las 15 pruebas + el arreglo de la cota (abajo). **El instalador de X.0.2 no está armado todavía**, a propósito, para no confundirlo con el que Mike ya tiene instalado.

Dos consecuencias de la línea X que hay que conocer:

- **Una entrega X no busca actualizaciones.** `mas_nueva()` sólo mira dígitos y leería «X.0.1» como «0.1»: avisaría de versión nueva en cada arranque. Lo apaga `es_de_pruebas()` en `core/actualizar.py`.
- **`package.json` sigue diciendo `0.20.1`** porque electron-builder exige semver. La versión que ve el taller sale de `core/version.py`, que es el único lugar donde se declara.

## Cómo se arma el instalador

En Linux, con Node 22 y Python 3.11:

```
npm install
apt-get install wine wine32     # ver abajo: hace falta el de 32 bits
npx electron-builder --win nsis  # deja dist/draw101-X.0.2-setup.exe
```

Cuatro cosas que costaron un intento cada una y no conviene volver a descubrir:

1. **Hace falta wine, y de 32 bits.** No es para firmar: NSIS fabrica el desinstalador **corriendo el instalador una vez**, y el instalador es x86. Con sólo wine de 64 bits falla con `failed to load ntdll.dll`. Son `dpkg --add-architecture i386` y `wine32`.
2. **`signAndEditExecutable: false`.** Sin eso electron-builder llama a `rcedit` y pide wine antes de empezar. El costo: el `.exe` conserva el icono de Electron; el de draw101 sí sale en la ventana, la barra de tareas y los accesos directos, que es donde se ve.
3. **`asar: false`.** `electron/main.js` arranca `server.py` como archivo de disco junto a `electron/`. Dentro de un asar no hay archivo que arrancar.
4. **`extraResources` copia `dwgjs/node_modules` a mano.** electron-builder saca cualquier `node_modules` de los globs de `files`, sin avisar. La primera entrega salió con buena cara —118 MB, instalador válido— y **sin los dos motores de DWG**.

Para moverlo se parte en pedazos de 19 MB (`split -b 19922944 -d -a 3`) y `UNIR-X.bat` los junta del lado de Windows comprobando tamaño y SHA-256.

## Las pruebas

Quince pruebas, **341 comprobaciones**, unos 50 segundos: `python verificar.py`. El detalle de cada una está en `pruebas/LEEME.md`.

Tres reglas de cómo están escritas, que conviene respetar al agregar más:

- **Cada comprobación dice qué debería pasar, en el idioma del taller.** No hay `assertEqual(a, b)`: hay «el bulge del vértice curvo vuelve igual (un arco no se aplana)».
- **Las de interfaz arrancan el programa de verdad** — servidor en un puerto libre y un Chromium con Playwright que dibuja con clics sobre el lienzo (`pruebas/navegador.py`). Si no hay Playwright, o no hay Node para las de DWG, esas pruebas se saltan diciéndolo en vez de fallar.
- **También se comprueba el control.** Donde una prueba dice «aquí NO tiene que pasar nada» se comprueba al lado que en el caso normal sí pasa.

Ninguna prueba escribe en la carpeta del usuario: `verificar.py` apunta `HOME` a un temporal antes de importar nada.

## Lo que las pruebas cazaron

**Arreglado — la cota que se iba de lado al estirar.** Al estirar por un extremo una pieza acotada, la línea de cota se movía siguiendo un traslado que nunca ocurrió (300 mm en el caso de prueba). Sólo se apuntaba el desplazamiento de los puntos que *cambiaban*, así que un estirado quedaba con un solo desplazamiento en la lista y «todos iguales» se cumplía sola. El código decía la intención correcta —«si la pieza se estiró o giró, sólo siguen los puntos ligados»— y hacía lo otro. Arreglado en `core/cotas.py`; `t008` lo deja clavado con el caso del traslado al lado.

**Abierto, y es decisión de Mike — `encapar` no vive donde dice vivir.** La regla «toda cota nace en COTAS» está escrita en el motor, pero la aplica quien crea la entidad (`server.py`), no `Documento.agregar`. Hoy no hay nada roto porque todo pasa por ahí; una cota creada llamando al documento directamente se quedaría en la capa activa. **No se cambió** porque mover la regla a `agregar` tocaría también la lectura de planos ajenos, y forzar las cotas de un arquitecto a nuestra capa es lo contrario de lo que hace el resto del diseño.

## El tema abierto: fluidez  ·  objetivo 1

Mike, después de probar X.0.1: *«Sigo teniendo de repente problemas en el "snappyness" del programa, pero funciona.»* El objetivo 1 de draw101 es la usabilidad fluida.

### Lo que ya está medido

Con un plano sintético del tamaño del Mondelez de verdad (leído del `.t101b`: 15 587 entidades, 39 788 trazos, 335 001 vértices; el sintético quedó en 21 757 entidades y 304 056 primitivas), corriendo draw101 completo en un navegador:

| Qué se midió | Cuánto cuesta |
| --- | --- |
| pintar el plano completo | **66–84 ms** |
| …de eso, recorrer los trazos en JavaScript | **1.4 ms** |
| pan y zoom (sobre la foto de Regen) | **0.0 ms** |
| armar el índice espacial, la primera vez | **550 ms** |
| aplicar el parche de una edición, con el índice ya armado | **0.9 ms** |
| borrar una entidad en el motor | 50 ms |
| osnap por movimiento del ratón | 0.4 ms |
| abrir el plano | 10 s en el motor + 6.6 s en cargar la interfaz |

**Salvedad importante:** salen de una máquina sin tarjeta de video, donde Chromium pinta por software (SwiftShader, 2 núcleos). Los milisegundos absolutos son pesimistas; **el reparto entre ellos no**.

### Lo que dicen

1. **El cuello es la rasterización del lienzo, no el código.** De los 66–84 ms, 1.4 son recorrer 21 757 trazos en JavaScript; el resto es Canvas 2D dibujando ruta por ruta. Eso es exactamente lo que un motor GPU convierte en unas pocas *draw calls*.
2. **Un motor nativo no arregla lo demás.** Los 550 ms del índice son JavaScript puro y se pagan a la primera interacción después de abrir; el abrir son 16 s entre motor e interfaz; y cualquier camino que en vez de parche haga recarga completa vuelve a pagar los dos. Con OpenGL siguen ahí igualitos.
3. **Pan y zoom ya están resueltos** por Regen (navegar sobre la foto): 0 ms. Lo que cuesta es el repintado completo después de cada edición.

### Las tres opciones

- **A · Prototipo C++/OpenGL (`t101cpp`).** **Ya existe y está compilado**: `t101cpp.exe`, ~900 líneas, con `A8-501.t101b` y `Mondelez.t101b` de prueba. No es un CAD — sólo ver, navegar, seleccionar, mover, deshacer y medir; sin osnap, cotas, capas, comandos, guardar ni DWG. Sirve para **medir el techo**, no para sustituir la app.
- **B · WebGL dentro de draw101.** El mismo salto a GPU cambiando el pintor de Canvas 2D a WebGL, sin salir de Electron, sin binario nuevo, sin perder osnap, cotas, capas ni DWG — que es todo lo que A tendría que reconstruir desde cero.
- **C · Atacar lo que no es pintado**: el índice de 550 ms, los 16 s de abrir, y auditar qué operaciones caen en recarga completa en vez de parche.

El prototipo demuestra que la GPU resuelve el problema de pintado. **No demuestra que haya que irse a C++ para usarla.**

### Lo que falta para decidir, y sólo Mike puede darlo

En su máquina, con su plano de verdad:

1. `DIAG ON`, trabajar normal. Anota cada cuadro de más de 40 ms con su desglose — está hecho para el «se puso lentísimo hace rato y ahora no se reproduce».
2. Cuando se ponga pesado, `PERF`. Escribe el informe y lo copia al portapapeles.
3. `A8-501.t101b` en `t101cpp.exe`, tecla `P`, y el mismo plano en draw101 con `PERF`. Los dos informes, lado a lado, son la comparación que el prototipo existe para dar.

## Qué hay en la carpeta t101d

```
t101d\
  draw101-fuente-X.0.2.zip     el proyecto completo (900 archivos, 6.5 MB)
  draw101-estado-X.0.1.md      cómo se recuperó y cómo se arma
  draw101-pruebas.md           qué cubre cada prueba
  draw101 handoff              este documento
  instalador\
    draw101-X.0.1-setup.exe.001..006  +  UNIR-X.bat
    draw101-0.20.1-setup.exe          la entrega anterior (de aquí salió la fuente)
    ...0.19.x y 0.20.0 en pedazos, y t101draw-0.18.x
  t101cpp\                     el prototipo C++/OpenGL + los dos .t101b de prueba
  sitio\                       el sitio Netlify que contesta oda.json
  suite101-tipografia-cifras.md
  draw101-herramientas.pdf · draw101-estimado-recursos.pptx
```

En el proyecto de Claude están además `claude/draw101-estado.md` y los estados de las otras apps.

## Pendientes, en orden

1. **El repo.** Crear `draw101` en GitHub y subir la fuente. Todo lo demás depende de esto.
2. **Decidir la fluidez** con los informes de `PERF`, `DIAG` y `t101cpp`.
3. **Armar X.0.2** cuando convenga (un comando) y probarla en Windows.
4. **Resolver `encapar`**: dejarlo como está o moverlo a `Documento.agregar`.
5. **Lo que ya venía pendiente**: más DWG de verdad, comprobar el DXF nuestro en AutoCAD y en Rhino, y una cocina real por `T101X` y luego `ACT`.
6. **El puente con suite101**: draw101 no habla todavía con la base unificada (Cloudflare Durable Objects / OrgDB). La feature 74 deja el paquete para SUPERVISOR en una carpeta y ahí se queda.

## Convenciones que no se negocian

- **El `.t101d` es el trabajo; el DXF es la entrega.** Para entregar, DXF — el DWG que escribimos no lo escribió Autodesk.
- **Nada se pierde en silencio.** Lo que el modelo no entiende se conserva tal cual y sale intacto al exportar.
- **El osnap trabaja sobre geometría exacta, no sobre lo que se pinta**, e ignora a propósito lo ajeno teselado (`aprox`). Seleccionar no necesita exactitud; medir sí.
- **Toda cota nace en `COTAS`.**
- **Lo blanco se imprime negro.**
- **La versión se declara en un solo lugar** (`core/version.py`) y no se repite número si el código cambió. Hasta la 0.9.0 salieron ocho instaladores distintos con el mismo nombre.
- **Los números de una medida van en Fira Sans** (cifras alineadas), el texto en Raleway, los títulos en Sansation. Norma de toda la suite; en draw101 está aplicada desde 0.18.x.
