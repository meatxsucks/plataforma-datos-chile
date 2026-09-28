#!/usr/bin/env bash
# Corre un job de Glue en la imagen oficial apuntando al S3 y al catálogo de floci.
# Uso: scripts/glue_local.sh <job> --arg1 valor1 --arg2 valor2 ...
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
JOB="$1"; shift
set -a; source "$RAIZ/.env"; set +a

docker run --rm \
  --network plataforma-datos-chile_default \
  -v "$RAIZ":/home/hadoop/workspace \
  -e AWS_ACCESS_KEY_ID=test \
  -e AWS_SECRET_ACCESS_KEY=test \
  -e AWS_REGION=us-east-1 \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e AWS_ENDPOINT_URL=http://floci:4566 \
  public.ecr.aws/glue/aws-glue-libs:5 \
  spark-submit \
    --driver-memory "${MEMORIA_DRIVER:-2g}" \
    --conf spark.hadoop.fs.s3.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
    --conf spark.hadoop.fs.s3a.endpoint=http://floci:4566 \
    --conf spark.hadoop.fs.s3a.path.style.access=true \
    --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
    --conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider \
    --conf spark.hadoop.fs.s3a.access.key=test \
    --conf spark.hadoop.fs.s3a.secret.key=test \
    --py-files /home/hadoop/workspace/utils/glue_utils.py \
    "/home/hadoop/workspace/glue/jobs/$JOB.py" \
    --JOB_NAME "$JOB" \
    "$@"
