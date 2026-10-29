#!/usr/bin/env bash
# Empaqueta una Lambda con sus dependencias para Python 3.12 en arm64.
# Uso: plataforma/scripts/empaquetar_lambda.sh <nombre>
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
ORIGEN=$(ls -d "$RAIZ"/plataforma/lambdas/"$1" "$RAIZ"/dominios/*/lambdas/"$1" 2>/dev/null | head -1)
DESTINO="$RAIZ/plataforma/terraform/.build/$1"

rm -rf "$DESTINO" && mkdir -p "$DESTINO"
if [ -f "$ORIGEN/requirements.txt" ]; then
  "$RAIZ/.venv/bin/pip" install --quiet -r "$ORIGEN/requirements.txt" --target "$DESTINO" \
    --platform manylinux2014_aarch64 --implementation cp --python-version 3.12 --only-binary=:all:
fi
cp "$ORIGEN"/*.py "$DESTINO"/
echo "$DESTINO"
