#!/usr/bin/env bash
# Crea una API key, la asocia al plan de uso y guarda su valor en .env.
# Se hace por CLI porque floci no devuelve las fechas de la key y el provider de Terraform falla al leerla.
# Uso: scripts/crear_api_key.sh <nombre>
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
NOMBRE="${1:-pdc-cliente-demo}"
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 AWS_ENDPOINT_URL=http://localhost:4566

PLAN=$(terraform -chdir="$RAIZ/infra/terraform" output -raw id_plan_uso)
for id in $(aws apigateway get-api-keys --name-query "$NOMBRE" --query 'items[].id' --output text); do
  aws apigateway delete-api-key --api-key "$id"
done
ID=$(aws apigateway create-api-key --name "$NOMBRE" --enabled --query id --output text)
aws apigateway create-usage-plan-key --usage-plan-id "$PLAN" --key-id "$ID" --key-type API_KEY >/dev/null
VALOR=$(aws apigateway get-api-key --api-key "$ID" --include-value --query value --output text)

sed -i '' '/^API_KEY_DEMO=/d' "$RAIZ/.env"
echo "API_KEY_DEMO=$VALOR" >> "$RAIZ/.env"
echo "API key $NOMBRE creada y guardada en .env como API_KEY_DEMO"
