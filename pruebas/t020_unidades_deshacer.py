"""t020 · Cambiar unidades es un paso del historial, y se deshace en orden.

Mike (14-sep-2026): «Hice polilíneas, cambié las unidades de mm a cm, me cambió
los tamaños del dibujo, le di Ctrl+Z y desaparecieron las polilíneas que
acababa de generar, pero también las líneas separadas, y no hay manera de
recuperarlas».

Causa: el cambio de unidades escalaba todo EN SILENCIO (sin anotar nada en el
historial). Ctrl+Z no deshacía las unidades sino la acción anterior, y la
restauraba con los números de antes de escalar: entidades en milímetros
dentro de un plano ya en centímetros, diez veces más lejos, «desaparecidas».

Ahora el cambio se anota como un paso: deshacer devuelve unidades y tamaños,
y lo demás sigue en orden. Prueba de motor, sin navegador.
"""

from __future__ import annotations

from core import unidades as mod_unidades
from core.documento import Documento
from core.entidades import de_dict
from pruebas import comun

DESCRIPCION = "cambiar unidades se deshace y no descoloca lo dibujado antes"


def correr(r: comun.Reporte) -> None:
    doc = Documento.nuevo()
    doc.unidades = "mm"
    # Los ids corren globales entre documentos: se toman de lo que devuelve agregar.
    lineas = []
    with doc.transaccion("Líneas"):
        for i in range(3):
            lineas.append(doc.agregar(de_dict({"tipo": "linea", "p1": [0, i * 100], "p2": [500, i * 100]})).id)
    with doc.transaccion("Unir"):          # como UNIR: se va una línea, entra una polilínea
        doc.borrar(lineas[0])
        poli = doc.agregar(de_dict({"tipo": "polilinea", "puntos": [[0, 0], [500, 0], [500, 100]], "cerrada": False})).id
    resto = sorted(lineas[1:] + [poli])

    with doc.transaccion("Cambiar unidades"):
        res = mod_unidades.cambiar(doc, "cm", True)
    r.igual(res["unidades"], "cm", "el dibujo pasa a cm")
    r.cierto(abs(res["factor"] - 0.1) < 1e-12, "con factor 0.1")
    r.punto(doc.entidades[poli].puntos[1][:2], [50, 0], "y la polilínea mide 50 cm donde medía 500 mm", 1e-9)
    r.cierto(doc.historial.puede_deshacer, "el cambio de unidades se puede deshacer")
    r.igual(doc.historial.nombre_deshacer(), "Cambiar unidades", "y es el primer paso que Ctrl+Z deshace")

    r.igual(doc.deshacer(), "Cambiar unidades", "Ctrl+Z 1: deshace las unidades")
    r.igual(doc.unidades, "mm", "vuelve a mm")
    r.cierto(doc.ultimo_toco_capas, "y avisa que tocó todo (el lienzo recarga completo)")
    r.punto(doc.entidades[poli].puntos[1][:2], [500, 0], "la polilínea vuelve a 500 mm", 1e-9)
    r.igual(sorted(doc.entidades), resto, "sin perder nada")

    r.igual(doc.deshacer(), "Unir", "Ctrl+Z 2: deshace el UNIR, en orden")
    r.igual(sorted(doc.entidades), sorted(lineas), "vuelven las tres líneas")
    r.punto(doc.entidades[lineas[0]].p2, [500, 0], "con sus medidas de mm, en un plano en mm: donde estaban", 1e-9)

    r.igual(doc.rehacer(), "Unir", "rehacer 1: el UNIR")
    r.igual(doc.rehacer(), "Cambiar unidades", "rehacer 2: las unidades")
    r.igual(doc.unidades, "cm", "otra vez en cm")
    r.punto(doc.entidades[poli].puntos[1][:2], [50, 0], "y la polilínea otra vez en 50", 1e-9)

    # Sin escalar: sólo cambia lo que significan los números; también se deshace.
    doc2 = Documento.nuevo()
    doc2.unidades = "mm"
    with doc2.transaccion("Línea"):
        linea = doc2.agregar(de_dict({"tipo": "linea", "p1": [0, 0], "p2": [600, 0]}))
    with doc2.transaccion("Cambiar unidades"):
        mod_unidades.cambiar(doc2, "m", False)
    r.punto(doc2.entidades[linea.id].p2, [600, 0], "sin escalar: los números se quedan")
    r.igual(doc2.unidades, "m", "pero el dibujo está en m")
    doc2.deshacer()
    r.igual(doc2.unidades, "mm", "y deshacer lo devuelve a mm")
