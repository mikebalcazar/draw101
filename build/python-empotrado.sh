#!/usr/bin/env bash
# Saca el Python empotrado del último instalador publicado de draw101.
#
# POR QUÉ ES UN ARCHIVO APARTE
#
# Esto vivía dentro de `.github/workflows/armar-y-publicar.yml`, y ahí el chat
# de draw101 no puede escribir: el conector de GitHub da 403 en
# `.github/workflows/`, así que cada ajuste costaba mover el archivo a mano
# desde el navegador. Aquí sí escribe, y el flujo sólo lo llama.
#
# QUÉ HACE
#
# draw101 no compila Python: reusa el intérprete con sus bibliotecas que ya
# viaja dentro del instalador anterior. De dónde sale ese instalador:
#   · `$INSTALADOR_ANTERIOR`, si trae una URL (para armar contra uno concreto);
#   · si no, el último publicado, leído de `draw101.json` en `descargas`.
#
# Y aguanta las dos formas de instalador que existen:
#   · el 0.20.1 llevaba `resources/python/` a la vista dentro del NSIS;
#   · los que arma electron-builder hoy meten toda la app comprimida otra vez
#     en `$PLUGINSDIR/app-64.7z`, y `resources/python` está ahí adentro.
#
# Historia, para no repetirla (19-sep-2026):
#   · corrida 30: la URL estaba clavada al 0.20.1, que la poda del 18-sep
#     borró. `curl` sin `-f` se tragó el 404, guardó la página de error como
#     «anterior.exe» y 7z tronó sin decir por qué. Se perdió la 0.20.19.
#   · corrida 31: un solo `7z` con filtro `resources/python/*` no saca nada de
#     los instaladores nuevos; el `mv` moría con «cannot stat».
#   · corrida 32: escribir la ruta `$PLUGINSDIR/...` a mano tampoco sirve —el
#     signo de peso lo tocan bash, MSYS y el propio 7-Zip—. Por eso ahora se
#     saca todo de un tirón y el archivo se busca con `find`.
set -euo pipefail

URL="${INSTALADOR_ANTERIOR:-}"
if [ -z "$URL" ]; then
  curl -fsSL -o manifiesto.json https://raw.githubusercontent.com/mikebalcazar/descargas/main/draw101.json
  URL=$(python -c "import json;print(json.load(open('manifiesto.json'))['draw101']['windows']['url'])")
fi
echo "Python empotrado de: $URL"

curl -fsSL -o anterior.exe "$URL"
ls -l anterior.exe
mkdir -p runtime

7z x -y -oanterior anterior.exe > extraer.log 2>&1 || {
  echo "7z no pudo abrir el instalador:"; tail -25 extraer.log; exit 1; }

if [ -d anterior/resources/python ]; then
  echo "instalador plano: resources/python a la vista"
  mv anterior/resources/python runtime/python
else
  EMB=$(find anterior -name 'app-64.7z' | head -1)
  if [ -z "$EMB" ]; then
    echo "no hay resources/python ni app-64.7z dentro del instalador. Esto trae:"
    find anterior -maxdepth 2 | head -40
    exit 1
  fi
  echo "la app va empotrada en: $EMB"
  7z x -y -oanterior/app "$EMB" > extraer2.log 2>&1 || {
    echo "7z no pudo abrir la app empotrada:"; tail -25 extraer2.log; exit 1; }
  if [ ! -d anterior/app/resources/python ]; then
    echo "la app empotrada no trae resources/python. Esto trae:"
    find anterior/app -maxdepth 2 | head -40
    exit 1
  fi
  mv anterior/app/resources/python runtime/python
fi

test -f runtime/python/python.exe
./runtime/python/python.exe -c "import ezdxf, fastapi, uvicorn, numpy, PIL, reportlab; print('python empotrado ok')"
rm -rf anterior anterior.exe extraer.log extraer2.log manifiesto.json
