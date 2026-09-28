#!/usr/bin/env bash
# Recrea el entorno MWAA después de reiniciar floci, que pierde el registro de sus contenedores.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
set -a; source "$RAIZ/.env"; set +a

docker ps -a --format '{{.Names}}' | grep 'floci-mwaa' | xargs -r docker rm -f >/dev/null
docker volume ls --format '{{.Name}}' | grep 'floci-mwaa' | xargs -r docker volume rm >/dev/null

TF_VAR_postgres_password="$POSTGRES_PASSWORD" TF_VAR_clave_seudonimo="$CLAVE_SEUDONIMO" \
  terraform -chdir="$RAIZ/infra/terraform" apply -replace=aws_mwaa_environment.principal -auto-approve -input=false

docker restart airflow-ui >/dev/null
