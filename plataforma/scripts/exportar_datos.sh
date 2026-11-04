#!/usr/bin/env bash
# Empaqueta los datos del stack local para llevarlos a otro PC: lago (floci-data), bodega Postgres, DocumentDB y tfstate.
# Uso: plataforma/scripts/exportar_datos.sh [carpeta_salida]   (por defecto ~/pdc-export)
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
set -a; source "$RAIZ/.env"; set +a
SALIDA="${1:-$HOME/pdc-export}"
mkdir -p "$SALIDA"

# floci puede dejar mas de un contenedor RDS: se usa el que tiene la bodega cargada
RDS=""
for c in $(docker ps --format '{{.Names}}' | grep '^floci-rds'); do
  docker exec "$c" psql -U pdc_admin -d bodega -tAc "select 1 from pg_tables where schemaname='dw' limit 1" 2>/dev/null | grep -q 1 && RDS="$c"
done
DOCDB="$(docker ps --format '{{.Names}}' | grep '^floci-docdb' | head -1)"
[ -n "$RDS" ] && [ -n "$DOCDB" ] || { echo "Levanta el stack primero (rds y docdb deben estar corriendo)"; exit 1; }

echo "1/4 Bodega Postgres"
docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$RDS" pg_dump -U pdc_admin -Fc bodega > "$SALIDA/bodega.dump"

echo "2/4 DocumentDB"
docker exec "$DOCDB" mongodump -u pdc_admin -p "$DOCDB_PASSWORD" --authenticationDatabase admin --archive --gzip > "$SALIDA/docdb.archive.gz"

echo "3/4 Lago (floci-data): se detiene floci para copiar consistente"
docker stop floci >/dev/null
tar -czf "$SALIDA/floci-data.tar.gz" -C "$HOME/.pdc" floci-data
docker start floci >/dev/null

echo "4/4 tfstate y .env (contiene secretos: no lo subas a ningun repo)"
cp "$RAIZ/plataforma/terraform/terraform.tfstate" "$SALIDA/"
cp "$RAIZ/.env" "$SALIDA/env"

( cd "$SALIDA" && shasum -a 256 * > SHA256SUMS )
du -sh "$SALIDA"/*
echo "Listo en $SALIDA. Copialo al otro PC (disco externo o rsync/scp)."
