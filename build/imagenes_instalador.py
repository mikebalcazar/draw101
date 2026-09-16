"""Las imágenes del instalador de Windows  ·  Mike (16-sep-2026): «en la
pantalla de instalación quiero algo con diseño, la ventana mientras se está
instalando el programa».

NSIS pide **BMP de 24 bits** con medidas exactas; un PNG no sirve y uno de 32
bits sale negro en algunos Windows. Se generan desde `assets/marca/draw101.png`
para que la carátula sea la marca de verdad y no un dibujo aparte que se quede
viejo:

    build/instalador-lateral.bmp      164 × 314   (bienvenida y despedida)
    build/instalador-encabezado.bmp   150 ×  57   (arriba, en cada paso)

Se corre solo desde el armado (`npm run dist` lo llama antes de empaquetar);
también a mano:

    python build/imagenes_instalador.py
"""

from __future__ import annotations

import pathlib

from PIL import Image

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MARCA = RAIZ / "assets" / "marca" / "draw101.png"

# Los colores de la casa (los mismos de ui/styles.css, tema oscuro).
TINTA = (26, 31, 39)
AZUL = (0, 128, 193)
AZUL_CLARO = (0, 169, 224)
NIEVE = (247, 249, 251)


def _degradado(ancho: int, alto: int, arriba, abajo) -> Image.Image:
    """Un fondo que va de un color a otro, de arriba abajo."""
    fondo = Image.new("RGB", (ancho, alto))
    px = fondo.load()
    for y in range(alto):
        t = y / max(1, alto - 1)
        color = tuple(int(arriba[i] + (abajo[i] - arriba[i]) * t) for i in range(3))
        for x in range(ancho):
            px[x, y] = color
    return fondo


def _pegar_marca(fondo: Image.Image, ancho_marca: int, centro_y: int) -> None:
    """La marca, a lo ancho que se le diga, centrada en horizontal."""
    marca = Image.open(MARCA).convert("RGBA")
    alto = max(1, round(marca.height * ancho_marca / marca.width))
    marca = marca.resize((ancho_marca, alto), Image.LANCZOS)
    fondo.paste(marca, ((fondo.width - ancho_marca) // 2, centro_y - alto // 2), marca)


def lateral(destino: pathlib.Path) -> pathlib.Path:
    """164 × 314: la franja de la izquierda en la bienvenida y al terminar."""
    im = _degradado(164, 314, TINTA, (10, 13, 18))
    # Una línea de acento a la derecha, como el filo de los paneles de la app.
    for y in range(314):
        for x in range(161, 164):
            im.putpixel((x, y), AZUL if y % 3 else AZUL_CLARO)
    _pegar_marca(im, 120, 120)
    # Y unas rayas finas abajo, guiño al plano: se ven, no gritan.
    for i, y in enumerate(range(232, 286, 12)):
        largo = 96 - i * 16
        for x in range(34, 34 + max(16, largo)):
            im.putpixel((x, y), (54, 66, 82))
    im.save(destino, "BMP")
    return destino


def encabezado(destino: pathlib.Path) -> pathlib.Path:
    """150 × 57: la esquina de arriba, visible en todos los pasos."""
    im = _degradado(150, 57, NIEVE, (233, 239, 245))
    _pegar_marca(im, 104, 28)
    for x in range(150):
        im.putpixel((x, 56), AZUL)
    im.save(destino, "BMP")
    return destino


def main() -> None:
    lateral(RAIZ / "build" / "instalador-lateral.bmp")
    encabezado(RAIZ / "build" / "instalador-encabezado.bmp")
    print("instalador-lateral.bmp (164×314) e instalador-encabezado.bmp (150×57) listos")


if __name__ == "__main__":
    main()
