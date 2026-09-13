# fluidez · camino C — lo que se midió y lo que cambia (13-sep-2026)

Mike eligió el camino C (atacar lo que no es pintado) el 13-sep. Esta rama trae
el resultado en `claude/fluidez-c.patch` (aplica limpio sobre `main` =
`0babf359`) + `pruebas/carga/sintetico.py`. `claude/APLICAR.txt` apunta al parche
para que `armar-y-publicar.yml` lo aplique si se arma desde esta rama.

## Medido (plano sintético de 21 700 entidades, 425 000 vértices; Linux, sin GPU)

| Qué | Motor | Interfaz | Parche |
|---|---|---|---|
| mover 1 entidad | 23 ms | 16 ms | sí |
| deshacer | 24 ms | 14 ms | sí |
| mover 300 | 68 ms | 8 ms | sí |
| borrar 300 / deshacer | 38 / 63 ms | 10 / 6 ms | sí |
| índice rehacer | — | 90–200 ms | — |
| recarga completa (`/api/trazos`, 24 MB, orjson) | 0.4 s | 0.6 s | — |
| pintar cuadro completo | — | 30–60 ms | — |

Ninguna operación de edición recarga completo; todas van por parche. El «de
repente se traba» no se reprodujo aquí: hace falta el informe de PERF en la
máquina de Mike, y por eso el segundo cambio.

## Cambios

1. **Segmentación de arcos por radio** (`core/dibujo.py`). 390 000 de los
   425 000 vértices eran círculos/arcos a 72 segmentos fijos. Ahora: tantos como
   pida no separarse más de 0.05 mm de la curva, entre 6 y 72 por vuelta
   (⌀5 → 16, ⌀20 → 32, ≥ ⌀100 → 72). En planos con muchos barrenos baja lo
   que se pinta, que es el cuello medido en el handoff.
2. **PERF anota las llamadas al motor** (`ui/base.js`, `ui/comandos.js`): cada
   llamada > 150 ms o que obligue a recarga completa queda con ruta, ms y KB, y
   PERF las imprime junto a los cuadros lentos. Es la mitad del diagnóstico
   que faltaba.
3. `pruebas/carga/sintetico.py`: fabrica el plano de prueba, determinista.

## Descartado por medición

Redondear coordenadas a milésimas: JSON 19 → 12 MB, pero +0.6 s de Python por
apertura y sin ganancia medible en el navegador; además rompía los grips
(comparan con la entidad exacta a 1e-6; t007 lo cazó). Queda anotado en
`dibujo.py` para que no se repita.

## Pruebas

`python verificar.py` con el parche: 18 pruebas, 382 comprobaciones, verdes.

## Huellas (sha256 tras aplicar el parche y añadir el guion)

- `core/dibujo.py` `decb5d6b95d7cd0aa45231e6fb9981f380405214a1a8fa6ff217488532cb40d6`
- `ui/base.js` `a46cc10b31bd8de574717eceab3e34e323c9c5cc50e29f38d2988b08e0e2dc15`
- `ui/comandos.js` `f8c7da00c68e860e7867670243c0736a3502fa1e4ee3864e552d2340450e68aa`
- `pruebas/carga/sintetico.py` `fd44134fbf51e48ff2191ee9f939df22f3cca5e2f4a12125954b20927ca12094`
