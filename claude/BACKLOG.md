# Backlog abierto de draw101 (modo acumulación)

Mike, 16-sep-2026: «vamos a empezar a hacer backlogs hasta que te pida que
integres todo en una versión nueva para publicar».

Aquí se van dejando los pedidos **ya programados y probados**, cada uno con su
parche y sus pruebas, **sin subir `core/version.py` ni `package.json`** y sin
disparar publicación. Cuando Mike diga, se juntan en una versión, se corre la
suite completa y se publica.

## Pedidos y estado

| # | Pedido | Estado |
|---|---|---|
| B1 | Pantalla del instalador con diseño | pendiente |
| B2 | Asociar DXF y DWG a draw101 | pendiente |
| B3 | Flechita visible para desplegar la consola | pendiente |
| B4 | Paleta de colores y selector RGB (capa y entidad) | **hecho** (`B10-paleta-color.patch`, `ui/color.js`, `pruebas/t030`) |
| B5 | Previa («fantasma») en TODAS las herramientas | pendiente, por tandas |
| B6 | «Guardar como…» con DXF y DWG | publicado en 0.20.14 |
| B7 | Pestañas siempre visibles | publicado en 0.20.14 |
| B8 | DWG que abre en blanco (capas apagadas) | publicado en 0.20.14 |
| B9 | Planos grandes: 50 → 30 MB al lienzo | publicado en 0.20.14 |

## Lo que sigue en rendimiento (medido, no hecho)

En el plano de Mike, **6 294 entidades generan 209 153 trazos** sueltos (una
sola llega a 24 043): son rayados y bloques explotados en segmentos. Unirlos por
entidad, o mandar cada bloque una vez y luego sólo sus inserciones, es el
siguiente salto de verdad; toca el pintor y el índice, así que va aparte.
Medido también: armar una hoja cuesta 0.6 s con la caché caliente y 4.5 s la
primera (ahí se construyen los trazos del modelo entero).

## Orden de aplicación

Los parches `B*` se aplican **después** de los `0.20.*`, en orden numérico de
B. Al integrar: añadirlos a `APLICAR.txt`, subir la versión una sola vez y
correr la suite completa antes de disparar la publicación.
