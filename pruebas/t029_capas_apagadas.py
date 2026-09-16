"""t029 · Un plano cuyas capas vienen todas apagadas se abre y se ve.

Mike (16-sep-2026) mandó un DWG de 24 MB («WP-MNDLZ-CARPINTERIAS-DC_-BIND»)
que nunca se dibujaba: el PERF decía «0 trazos, 0 primitivas». El archivo se
leía bien —15 972 entidades— pero 134 de sus 136 capas llegaban apagadas y
sólo quedaban 54 entidades visibles.

La culpa es del convertidor: libredwg escribe el color de cada capa en
negativo, y en DXF un color negativo significa «capa apagada». Un plano con
todas las capas apagadas no existe —nadie dibuja algo para no verlo—, así que
cuando la proporción es absurda (≥ 90 % de al menos cinco capas) se encienden
todas y se anota en el informe.

Se comprueba con un DXF fabricado aquí: uno con todas las capas apagadas (se
encienden y se avisa) y otro donde apagar una capa es una decisión de verdad
(no se toca).
"""

from __future__ import annotations

import pathlib
import tempfile

import ezdxf

from core import dxf_lector
from pruebas import comun

DESCRIPCION = "capas que el convertidor apaga en masa se encienden al abrir"


def _fabricar(ruta: pathlib.Path, apagadas: int, total: int = 30) -> None:
    """Un DXF con `total` capas, `apagadas` de ellas apagadas (color negativo,
    que es como lo escribe libredwg), y una línea en cada una. Ojo: ezdxf pone
    además «0» y «Defpoints», encendidas, así que el porcentaje se cuenta sobre
    `total + 2`."""
    d = ezdxf.new(setup=False)
    msp = d.modelspace()
    for i in range(total):
        nombre = f"CAPA{i}"
        capa = d.layers.add(nombre)
        capa.dxf.color = -7 if i < apagadas else 7
        msp.add_line((0, i * 10), (100, i * 10), dxfattribs={"layer": nombre})
    d.saveas(ruta)


def correr(r: comun.Reporte) -> None:
    carpeta = pathlib.Path(tempfile.mkdtemp())

    # 1. Como el plano de Mike: casi todas apagadas → se encienden.
    ruta = carpeta / "todas-apagadas.dxf"
    _fabricar(ruta, apagadas=30, total=30)
    doc, inf = dxf_lector.leer_dxf(ruta)[:2]
    r.igual(len(doc.capas), 32, "el DXF trae sus treinta capas (más «0» y «Defpoints»)")
    r.igual(len(doc.visibles("")), 30, "y las treinta entidades se ven, no cero")
    r.cierto(any("capas apagadas" in a for a in inf.avisos),
             "y el informe dice que se encendieron y por qué")

    # 2. Veintinueve de treinta (más las dos de ezdxf): 91 %, sigue siendo absurdo.
    ruta = carpeta / "casi-todas.dxf"
    _fabricar(ruta, apagadas=29, total=30)
    doc = dxf_lector.leer_dxf(ruta)[0]
    r.igual(len(doc.visibles("")), 30, "con 29 de 32 apagadas también se encienden")

    # 3. Apagar capas como decisión de verdad: no se toca.
    ruta = carpeta / "algunas.dxf"
    _fabricar(ruta, apagadas=12, total=30)
    doc = dxf_lector.leer_dxf(ruta)[0]
    r.igual(len(doc.visibles("")), 18, "doce de treinta apagadas se respetan: se ven dieciocho")
    apagadas = [c for c in doc.capas.values() if not c.visible]
    r.igual(len(apagadas), 12, "y las doce siguen apagadas")

    # 4. Un archivo chico (menos de cinco capas) tampoco se toca: ahí apagar
    # una capa es a mano y se nota.
    ruta = carpeta / "chico.dxf"
    _fabricar(ruta, apagadas=2, total=2)
    doc = dxf_lector.leer_dxf(ruta)[0]
    r.igual(len(doc.visibles("")), 0, "en un plano de dos capas apagadas se respeta la decisión")
