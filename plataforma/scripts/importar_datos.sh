#!/usr/bin/env bash
# Restaura en un PC nuevo lo que genero exportar_datos.sh. Requiere el repo clonado, Docker, terraform y el stack apagado.
# Uso: plataforma/scripts/importar_datos.sh carpeta_con_export
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
ORIGEN="${1:?Indica la carpeta con el export}"
( cd "$ORIGEN" && shasum -a 256 -c SHA256SUMS )

echo "1/5 Archivos de configuracion"
cp "$ORIGEN/env" "$RAIZ/.env"
cp "$ORIGEN/terraform.tfstate" "$RAIZ/plataforma/terraform/terraform.tfstate"
set -a; source "$RAIZ/.env"; set +a

echo "2/5 Lago: floci-data en ~/.pdc"
mkdir -p "$HOME/.pdc"
[ -e "$HOME/.pdc/floci-data" ] && { echo "~/.pdc/floci-data ya existe; muevelo o borralo a mano"; exit 1; }
tar -xzf "$ORIGEN/floci-data.tar.gz" -C "$HOME/.pdc"

echo "3/5 Levantar el stack (floci reconstruye RDS y DocumentDB desde su estado)"
cd "$RAIZ" && docker compose up -d --build
sleep 25
docker ps -a --format '{{.Names}}' | grep -E '^floci-(rds|docdb)' | xargs -r docker start >/dev/null
sleep 15

echo "4/5 Restaurar bodega y DocumentDB"
RDS="$(docker ps --format '{{.Names}}' | grep '^floci-rds' | tail -1)"  # tras importar solo deberia haber uno
DOCDB="$(docker ps --format '{{.Names}}' | grep '^floci-docdb' | head -1)"
docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" "$RDS" pg_restore -U pdc_admin -d bodega --clean --if-exists --no-owner < "$ORIGEN/bodega.dump" || echo "pg_restore reporto avisos (suelen ser roles ausentes): revisa que existan dw, stage y monitoreo"
docker exec -i "$DOCDB" mongorestore -u pdc_admin -p "$DOCDB_PASSWORD" --authenticationDatabase admin --archive --gzip --drop < "$ORIGEN/docdb.archive.gz"

echo "5/5 Recrear Airflow y publicar DAGs"
bash "$RAIZ/plataforma/scripts/recrear_mwaa.sh"
bash "$RAIZ/plataforma/scripts/publicar_dags.sh"
echo "Listo. Airflow http://localhost:8080  Grafana http://localhost:3000"
