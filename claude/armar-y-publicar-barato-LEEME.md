# El workflow barato: mover esto a `.github/workflows/armar-y-publicar.yml`

Mike (16-sep-2026): «se consumieron muy rápido los deploys», y decidió dejar el
repo **privado**. Este archivo es el mismo flujo de siempre con cuatro cambios
que bajan la cuota sin cambiar el resultado. El chat no puede escribir en
`.github/workflows` (403), así que lo mueve Mike desde la web o Jr. con `git mv`.

**Desde la web, un minuto:** abrir este archivo en la rama `claude/0.20.16`,
tocar el lápiz, cambiar el nombre a `.github/workflows/armar-y-publicar.yml`,
borrar estas primeras líneas (hasta la raya) y Commit.

Qué cambia y cuánto ahorra:

1. **`ubuntu-latest` con wine en vez de `windows-latest`.** GitHub cobra los
   minutos de Windows al doble: 40 min de run eran ~80 de cuota. Con wine el run
   baja a ~10 min y cuenta ×1: **ocho veces más barato**. El instalador sale
   igual —así se armaron las 0.20.2, 0.20.3 y 0.20.4, que Mike instaló sin
   problema— porque quien arma el NSIS es electron-builder, no Windows. El chat
   armó así la 0.20.16 antes de escribir esto: 119 312 606 bytes, con la
   carátula nueva dentro (comprobado píxel por píxel contra
   `build/instalador-lateral.bmp`).
2. **Las pruebas no se repiten en el runner.** Las 30 ya pasan en el chat antes
   de disparar; aquí se llevaban la mitad del run. Queda el interruptor
   `con_pruebas` en el disparo a mano, por si alguna vez hace falta.
3. **Sin artefacto.** Eran 125 MB por run y el instalador termina en
   `descargas`, que es de donde se baja.
4. Se conserva lo que importa: comprobar versión, motores DWG, Python empotrado,
   y **bajar lo publicado y comparar su sha256** antes de tocar el manifiesto.

---
