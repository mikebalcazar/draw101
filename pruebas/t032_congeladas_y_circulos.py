"""t032 · Capas congeladas y círculos redondos.

Mike (17-sep-2026) abrió un DWG suyo («TO-Penthouse») y el plano salía lleno de
rayas amarillas y rojas que en AutoCAD no están, y con las burbujas de los ejes
hechas hexágonos. Dos fallas distintas, las dos de la 0.20.14:

  · **Congeladas.** El archivo trae cinco capas de un levantamiento
    topográfico que alguien congeló. Congelar y apagar se parecen al mirar el
    plano, pero en el DXF son cosas distintas (bandera 70 bit 1 contra color
    negativo) y draw101 sólo leía el apagado. Encima, el arreglo del 16-sep
    —que enciende las capas cuando el convertidor de DWG las marca apagadas de
    más— las resucitaba.
  · **Círculos poligonales.** Se les daba a los círculos los segmentos que
    pidiera su radio con una tolerancia de 0.05 mm, pero comparada contra el
    radio en las unidades del dibujo, sin convertir: en un plano en metros, una
    burbuja de radio 0.15 salía con seis lados. Se volvió a 72 por vuelta.
"""

from __future__ import annotations

import math
import pathlib
import tempfile

import ezdxf

from core import dxf_lector
from core.dibujo import trazos
from core.documento import Documento
from core.entidades import de_dict
from pruebas import comun

DESCRIPCION = "capas congeladas respetadas y círculos redondos a cualquier escala"


def correr(r: comun.Reporte) -> None:
    _congeladas(r)
    _circulos(r)


def _fabricar(ruta: pathlib.Path) -> None:
    """Un DXF con tres capas: una normal, una apagada y una congelada, con una
    línea en cada una. Los colores van en negativo, como los escribe el
    convertidor de DWG, para que también se pruebe el arreglo del 16-sep."""
    d = ezdxf.new(setup=False)
    msp = d.modelspace()
    for nombre, apagada, congelada in (("NORMAL", False, False),
                                       ("APAGADA", True, False),
                                       ("CONGELADA", False, True)):
        capa = d.layers.add(nombre)
        capa.dxf.color = -7 if apagada else 7
        if congelada:
            capa.freeze()
        msp.add_line((0, 0), (100, 0), dxfattribs={"layer": nombre})
    d.saveas(ruta)


def _congeladas(r: comun.Reporte) -> None:
    ruta = pathlib.Path(tempfile.mkdtemp()) / "capas.dxf"
    _fabricar(ruta)
    doc = dxf_lector.leer_dxf(ruta)[0]

    r.cierto(doc.capas["CONGELADA"].congelada, "la capa congelada se lee como congelada")
    r.cierto(not doc.capas["NORMAL"].congelada, "y la normal no")
    r.cierto(not doc.capas["APAGADA"].visible, "la apagada queda apagada")

    capas = {e.capa for e in doc.visibles("")}
    r.cierto("NORMAL" in capas, "lo de la capa normal se ve")
    r.cierto("CONGELADA" not in capas, "lo de la capa congelada NO se ve")
    r.cierto("APAGADA" not in capas, "y lo de la apagada tampoco")

    # Una capa congelada que además viene marcada apagada por el convertidor
    # sigue congelada: el arreglo del encendido no la resucita.
    doc.capas["CONGELADA"].visible = True
    r.cierto("CONGELADA" not in {e.capa for e in doc.visibles("")},
             "encender una capa congelada no la enseña: sigue congelada")

    # Y se guarda y se abre conservándolo.
    from core import proyecto
    p = ruta.with_suffix(".t101d")
    proyecto.guardar(doc, p)
    vuelto = proyecto.abrir(p)
    r.cierto(vuelto.capas["CONGELADA"].congelada, "el congelado sobrevive a guardar y abrir")


def _circulos(r: comun.Reporte) -> None:
    """Un círculo se ve redondo mida lo que mida: en un plano en metros, una
    burbuja de radio 0.15 tiene que traer los mismos lados que un barreno de
    radio 150 en uno en milímetros."""
    def lados(radio: float) -> int:
        doc = Documento.nuevo()
        e = doc.agregar(de_dict({"tipo": "circulo", "centro": [0, 0], "radio": radio}))
        t = [x for x in trazos(doc, "") if x["id"] == e.id][0]
        return len(t["puntos"]) - 1          # el último punto repite el primero

    chico, grande = lados(0.15), lados(150)
    r.igual(chico, grande, f"la burbuja de 0.15 trae los mismos lados que el barreno de 150 ({chico})")
    r.cierto(chico >= 64, f"y son bastantes: {chico} (un hexágono se ve hexágono)")

    # La flecha: qué tanto se separa la cuerda del círculo de verdad.
    doc = Documento.nuevo()
    e = doc.agregar(de_dict({"tipo": "circulo", "centro": [0, 0], "radio": 0.15}))
    pts = [x for x in trazos(doc, "") if x["id"] == e.id][0]["puntos"]
    a, b = pts[0], pts[1]
    medio = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    flecha = 0.15 - math.hypot(*medio)
    r.cierto(flecha / 0.15 < 0.01, f"la cuerda se separa menos del 1 % del radio ({flecha / 0.15:.4%})")
