/* Las imágenes del instalador de Windows, hechas con Node y nada más.
 *
 * POR QUÉ ESTE ARCHIVO EXISTE  ·  18-sep-2026
 *
 *   La carátula del instalador (B1 del backlog) son dos BMP de 24 bits que
 *   electron-builder exige encontrar en `build/`. Se generaban con
 *   `build/imagenes_instalador.py` (Pillow) al correr `npm run dist`. Pero el
 *   corredor de GitHub llama a `npx electron-builder` directo y en su Python no
 *   hay Pillow, y los BMP no van en el repo porque el conector del chat no
 *   sube binarios. Resultado: el armado 0.20.18 murió con «cannot find
 *   specified resource build/instalador-encabezado.bmp».
 *
 *   Este guion hace lo mismo sin depender de nada: lee el PNG del logotipo
 *   (`assets/marca/draw101.png`) con zlib, que Node trae de fábrica; lo
 *   escala; lo pega sobre el fondo; y escribe los BMP. Corre solo en
 *   `postinstall` (o sea, en cada `npm ci`), así que donde se instalen las
 *   dependencias están las imágenes, sin tocar el workflow.
 *
 *   Si algo falla (un PNG raro, lo que sea), escribe fondos lisos con la marca
 *   ausente y avisa, en vez de tumbar la instalación: un instalador sin
 *   logotipo es feo; un armado roto es peor.
 *
 *   Los colores son los de la casa (ui/styles.css, tema oscuro). Las medidas
 *   son las que NSIS exige: 164×314 el lateral, 150×57 el encabezado.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const RAIZ = path.resolve(__dirname, "..");
const MARCA = path.join(RAIZ, "assets", "marca", "draw101.png");

const TINTA = [26, 31, 39], AZUL = [0, 128, 193], AZUL_CLARO = [0, 169, 224];
const NIEVE = [247, 249, 251];

/* --- PNG: lo mínimo para leer un RGBA/RGB de 8 bits sin entrelazar --------- */
function leerPNG(ruta) {
  const b = fs.readFileSync(ruta);
  if (b.readUInt32BE(0) !== 0x89504e47) throw new Error("no es PNG");
  let pos = 8, ancho = 0, alto = 0, tipo = 0, prof = 0, entrelazado = 0;
  const idat = [];
  while (pos < b.length) {
    const largo = b.readUInt32BE(pos);
    const nombre = b.toString("ascii", pos + 4, pos + 8);
    const datos = b.subarray(pos + 8, pos + 8 + largo);
    if (nombre === "IHDR") {
      ancho = datos.readUInt32BE(0); alto = datos.readUInt32BE(4);
      prof = datos[8]; tipo = datos[9]; entrelazado = datos[12];
    } else if (nombre === "IDAT") idat.push(datos);
    else if (nombre === "IEND") break;
    pos += 12 + largo;
  }
  if (prof !== 8 || entrelazado !== 0 || (tipo !== 6 && tipo !== 2)) {
    throw new Error(`PNG no soportado (prof ${prof}, tipo ${tipo}, entrelazado ${entrelazado})`);
  }
  const canales = tipo === 6 ? 4 : 3;
  const crudo = zlib.inflateSync(Buffer.concat(idat));
  const fila = ancho * canales;
  const salida = Buffer.alloc(ancho * alto * 4);
  let anterior = Buffer.alloc(fila);
  for (let y = 0; y < alto; y++) {
    const filtro = crudo[y * (fila + 1)];
    const cur = Buffer.from(crudo.subarray(y * (fila + 1) + 1, (y + 1) * (fila + 1)));
    for (let i = 0; i < fila; i++) {
      const a = i >= canales ? cur[i - canales] : 0;
      const arr = anterior[i];
      const c = i >= canales ? anterior[i - canales] : 0;
      let v = cur[i];
      if (filtro === 1) v += a;
      else if (filtro === 2) v += arr;
      else if (filtro === 3) v += (a + arr) >> 1;
      else if (filtro === 4) {
        const p = a + arr - c, pa = Math.abs(p - a), pb = Math.abs(p - arr), pc = Math.abs(p - c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? arr : c);
      }
      cur[i] = v & 255;
    }
    for (let x = 0; x < ancho; x++) {
      const o = (y * ancho + x) * 4, i = x * canales;
      salida[o] = cur[i]; salida[o + 1] = cur[i + 1]; salida[o + 2] = cur[i + 2];
      salida[o + 3] = canales === 4 ? cur[i + 3] : 255;
    }
    anterior = cur;
  }
  return { ancho, alto, px: salida };
}

/* --- Un lienzo RGB sencillo ------------------------------------------------ */
function lienzo(ancho, alto) {
  return { ancho, alto, px: Buffer.alloc(ancho * alto * 3) };
}

function degradado(l, arriba, abajo) {
  for (let y = 0; y < l.alto; y++) {
    const t = y / Math.max(1, l.alto - 1);
    for (let x = 0; x < l.ancho; x++) {
      const o = (y * l.ancho + x) * 3;
      for (let k = 0; k < 3; k++) l.px[o + k] = Math.round(arriba[k] + (abajo[k] - arriba[k]) * t);
    }
  }
}

function punto(l, x, y, c) {
  if (x < 0 || y < 0 || x >= l.ancho || y >= l.alto) return;
  const o = (y * l.ancho + x) * 3;
  l.px[o] = c[0]; l.px[o + 1] = c[1]; l.px[o + 2] = c[2];
}

/* La marca escalada (bilineal) y pegada con su transparencia, centrada. */
function pegarMarca(l, marca, anchoMarca, centroY) {
  const escala = anchoMarca / marca.ancho;
  const altoMarca = Math.max(1, Math.round(marca.alto * escala));
  const x0 = Math.floor((l.ancho - anchoMarca) / 2), y0 = centroY - Math.floor(altoMarca / 2);
  for (let y = 0; y < altoMarca; y++) {
    for (let x = 0; x < anchoMarca; x++) {
      const sx = Math.min(marca.ancho - 1, x / escala), sy = Math.min(marca.alto - 1, y / escala);
      const ix = Math.floor(sx), iy = Math.floor(sy), fx = sx - ix, fy = sy - iy;
      const c = [0, 0, 0, 0];
      for (let k = 0; k < 4; k++) {
        const p = (xx, yy) => marca.px[(Math.min(marca.alto - 1, yy) * marca.ancho + Math.min(marca.ancho - 1, xx)) * 4 + k];
        c[k] = p(ix, iy) * (1 - fx) * (1 - fy) + p(ix + 1, iy) * fx * (1 - fy) +
               p(ix, iy + 1) * (1 - fx) * fy + p(ix + 1, iy + 1) * fx * fy;
      }
      const a = c[3] / 255;
      if (a <= 0) continue;
      const dx = x0 + x, dy = y0 + y;
      if (dx < 0 || dy < 0 || dx >= l.ancho || dy >= l.alto) continue;
      const o = (dy * l.ancho + dx) * 3;
      for (let k = 0; k < 3; k++) l.px[o + k] = Math.round(l.px[o + k] * (1 - a) + c[k] * a);
    }
  }
}

/* BMP de 24 bits, de abajo hacia arriba y con filas a múltiplo de 4, que es lo
 * que NSIS entiende. */
function escribirBMP(l, ruta) {
  const filaBytes = Math.ceil(l.ancho * 3 / 4) * 4;
  const datos = filaBytes * l.alto;
  const b = Buffer.alloc(54 + datos);
  b.write("BM", 0); b.writeUInt32LE(54 + datos, 2); b.writeUInt32LE(54, 10);
  b.writeUInt32LE(40, 14); b.writeInt32LE(l.ancho, 18); b.writeInt32LE(l.alto, 22);
  b.writeUInt16LE(1, 26); b.writeUInt16LE(24, 28); b.writeUInt32LE(0, 30);
  b.writeUInt32LE(datos, 34); b.writeInt32LE(2835, 38); b.writeInt32LE(2835, 42);
  for (let y = 0; y < l.alto; y++) {
    const fuente = l.alto - 1 - y;
    for (let x = 0; x < l.ancho; x++) {
      const o = (fuente * l.ancho + x) * 3, d = 54 + y * filaBytes + x * 3;
      b[d] = l.px[o + 2]; b[d + 1] = l.px[o + 1]; b[d + 2] = l.px[o];   // BGR
    }
  }
  fs.writeFileSync(ruta, b);
}

function lateral(marca) {
  const l = lienzo(164, 314);
  degradado(l, TINTA, [10, 13, 18]);
  for (let y = 0; y < 314; y++) for (let x = 161; x < 164; x++) punto(l, x, y, y % 3 ? AZUL : AZUL_CLARO);
  if (marca) pegarMarca(l, marca, 120, 120);
  for (let i = 0, y = 232; y < 286; y += 12, i++) {
    const largo = Math.max(16, 96 - i * 16);
    for (let x = 34; x < 34 + largo; x++) punto(l, x, y, [54, 66, 82]);
  }
  return l;
}

function encabezado(marca) {
  const l = lienzo(150, 57);
  degradado(l, NIEVE, [233, 239, 245]);
  if (marca) pegarMarca(l, marca, 104, 28);
  for (let x = 0; x < 150; x++) punto(l, x, 56, AZUL);
  return l;
}

function main() {
  let marca = null;
  try { marca = leerPNG(MARCA); }
  catch (e) { console.warn(`imagenes_instalador: sin logotipo (${e.message}); van los fondos lisos`); }
  const salida = path.join(RAIZ, "build");
  escribirBMP(lateral(marca), path.join(salida, "instalador-lateral.bmp"));
  escribirBMP(encabezado(marca), path.join(salida, "instalador-encabezado.bmp"));
  console.log("imagenes_instalador: instalador-lateral.bmp (164×314) e instalador-encabezado.bmp (150×57) listos");
}

if (require.main === module) {
  try { main(); }
  catch (e) { console.warn(`imagenes_instalador: ${e.message}`); }
}
