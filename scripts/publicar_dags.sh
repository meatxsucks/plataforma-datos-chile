#!/usr/bin/env bash
# Publica los DAGs en S3 y los copia al contenedor de Airflow.
# floci solo sincroniza desde S3 al crear el entorno; en MWAA real bastaría con subirlos al bucket.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 AWS_ENDPOINT_URL=http://localhost:4566

aws s3 sync --only-show-errors "$RAIZ/airflow/dags" s3://pdc-mwaa/dags --exclude "__pycache__/*"
AIRFLOW=$(docker ps --format '{{.Names}}' | grep 'pdc-airflow-airflow')
for dag in "$RAIZ"/airflow/dags/*.py; do
  docker cp "$dag" "$AIRFLOW:/opt/airflow/dags/"
done
docker exec "$AIRFLOW" airflow dags reserialize >/dev/null 2>&1
echo "DAGs publicados en s3://pdc-mwaa/dags y en $AIRFLOW"
