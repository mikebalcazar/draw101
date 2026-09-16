# Backlog abierto de draw101 (modo acumulación)

Mike, 16-sep-2026: «vamos a empezar a hacer backlogs hasta que te pida que
integres todo en una versión nueva para publicar».

Aquí se van dejando los pedidos **ya programados y probados**, cada uno con su
parche y sus pruebas, **sin subir `core/version.py` ni `package.json`** y sin
disparar publicación. Cuando Mike diga, se juntan en una versión, se corre la
suite completa y se publica.

Esta rama parte de `claude/0.20.13` (la última disparada). Los parches de
`claude/*.patch` de versiones anteriores siguen ahí y `APLICAR.txt` los lista
en orden; los del backlog se añaden al final con nombre `Bn-<tema>.patch`.

## Pedidos y estado

| # | Pedido | Estado |
|---|---|---|
| B1 | Pantalla del instalador con diseño | pendiente |
| B2 | Asociar DXF y DWG a draw101 | pendiente |
| B3 | Flechita visible para desplegar la consola | pendiente |
| B4 | Paleta de colores y selector RGB (capa y entidad) | pendiente |
| B5 | Previa («fantasma») en TODAS las herramientas | pendiente, por tandas |
| B6 | «Guardar como…» con DXF y DWG | **hecho** (`B6-guardar-como.patch`, `pruebas/t027`) |
| B7 | Pestañas siempre visibles, aunque haya un solo dibujo | **hecho** (`B7-pestanas-siempre.patch`, `pruebas/t028`) |

El detalle de cada uno, con las decisiones y las trampas conocidas, está en
Drive: `suite101/t101d/draw101-backlog-abierto-2026-09-16`.

## Orden de aplicación

Los parches `B*` se aplican **después** de los `0.20.*`, en orden numérico de
B. Al integrar: añadirlos a `APLICAR.txt`, subir la versión una sola vez y
correr la suite completa antes de disparar la publicación.
