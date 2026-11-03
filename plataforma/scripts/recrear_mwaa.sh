#!/usr/bin/env bash
# Recrea el entorno MWAA después de reiniciar floci, que pierde el registro de sus contenedores.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
set -a; source "$RAIZ/.env"; set +a

docker ps -a --format '{{.Names}}' | grep 'floci-mwaa' | xargs -r docker rm -f >/dev/null
docker volume ls --format '{{.Name}}' | grep 'floci-mwaa' | xargs -r docker volume rm >/dev/null

TF_VAR_postgres_password="$POSTGRES_PASSWORD" TF_VAR_clave_seudonimo="$CLAVE_SEUDONIMO" \
  TF_VAR_docdb_password="$DOCDB_PASSWORD" TF_VAR_openrouter_api_key="${OPENROUTER_API_KEY:-}" TF_VAR_dtpm_usuario="$DTPM_USUARIO" TF_VAR_dtpm_clave="$DTPM_CLAVE" \
  terraform -chdir="$RAIZ/plataforma/terraform" apply -replace=aws_mwaa_environment.principal -auto-approve -input=false

docker restart airflow-ui >/dev/null
