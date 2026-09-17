# Gastar menos cuota de GitHub al publicar  ·  16-sep-2026

Mike: «se consumieron muy rápido los deploys». Medido y explicado, con lo que
hay que cambiar y quién puede hacerlo.

## Dónde se va la cuota

- `descargas` es **público**: sus flujos son gratis. Lo caro es `draw101`, que
  es **privado**.
- El flujo corre en **`windows-latest`**, y GitHub cobra los minutos de Windows
  **al doble**. Cada publicación tarda ~40 min → **~80 minutos de cuota**.
- En dos días se publicaron ~16 versiones de draw101 (más las de nest101 y
  shape101, que hacen lo mismo en sus repos privados).
- Cada run guarda además el instalador como **artefacto de 125 MB**, 14 días.
  Eso no gasta minutos pero sí el espacio de Actions.

## Los cuatro cambios, por lo que ahorran

1. **Armar en Linux con wine en vez de Windows.** El chat armó así las 0.20.2,
   0.20.3 y 0.20.4 y Mike las instaló sin problema: `apt install wine wine32`,
   `npx electron-builder --win nsis`. En el corredor tarda ~10 min y Linux
   cuenta **×1**: de ~80 minutos de cuota por versión a ~10. **Ocho veces más
   barato**, y es el cambio que de verdad mueve la aguja.
2. **Quitar las pruebas del corredor.** Las 30 pruebas ya se corren en el chat
   antes de disparar; correrlas otra vez en Windows con Playwright cuesta la
   mitad del tiempo del run. Se deja la comprobación que sí importa: que el
   sha256 de lo publicado cuadre.
3. **No guardar el artefacto** (o `retention-days: 1`). El instalador termina en
   `descargas`, que es donde se baja; el artefacto era el respaldo de cuando no
   había token.
4. **Publicar menos veces.** Juntar el backlog y sacar una versión con varias
   cosas, en vez de una por pedido. Esto no es código, es cómo trabajamos, y lo
   adopta el chat.

## Lo que NO conviene

**Hacer público `draw101`** haría gratis los minutos, pero publica la fuente
completa del producto que Mike acaba de decidir **vender por suscripción**
(ver `draw101-licencias-etapa1-2026-09-16` en Drive). Los instaladores y las
publicaciones ya se ven, porque `descargas` es público; lo que se sumaría es el
código. Con los cambios 1 a 4 la cuota alcanza de sobra sin regalar eso.

## Releases viejas

Mike: «quedémonos sólo con las 3 últimas». Hoy en `descargas` hay **38
releases, 6.0 GB**: 14 de draw101, 11 de nest101, 8 de shape101, más las tres
etiquetas `*-ultima`. Lo que hay que borrar de draw101, dejando 0.20.14, 0.20.13
y 0.20.12 (y `draw101-ultima`, que nunca se toca):

    draw101-0.20.11  0.20.10  0.20.9  0.20.8  0.20.7  0.20.6  0.20.5
    draw101-0.20.4   0.20.3   0.20.2  0.20.1  0.20.0  0.19.4

El conector del chat no borra releases. Lo hace el chat de `descargas` o Jr. con
`gh release delete`, o Mike desde la web. Conviene dejarlo automático: un flujo
en `descargas` (que es público, o sea gratis) que al publicar borre lo que pase
de las tres últimas de cada programa.

## Quién hace qué

- **Mike o Jr.**: cambiar `.github/workflows/armar-y-publicar.yml` (el chat
  recibe 403 en esa carpeta). El archivo listo está en
  `claude/armar-y-publicar-barato.yml`.
- **Chat de draw101**: publicar menos veces, juntando el backlog.
- **Chat de descargas o Jr.**: la limpieza de releases.
