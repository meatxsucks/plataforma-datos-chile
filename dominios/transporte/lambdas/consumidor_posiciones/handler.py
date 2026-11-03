import base64
import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3

TABLA = os.environ["TABLA"]
BUCKET_RAW = os.environ["BUCKET_RAW"]


# Punto de entrada: un lote de registros de Kinesis
def handler(event, context):
    """Deja la última posición por patente en DynamoDB y guarda el lote como JSON lines en raw."""
    registros = [json.loads(base64.b64decode(r["kinesis"]["data"]), parse_float=Decimal) for r in event["Records"]]

    # shortcut: gana el último registro del lote por patente sin comparar fechas, mejorar si llegan datos desordenados
    with boto3.resource("dynamodb").Table(TABLA).batch_writer(overwrite_by_pkeys=["patente"]) as lote:
        for r in registros:
            lote.put_item(Item=r)

    ahora = datetime.now(timezone.utc)
    clave = f"transporte/posiciones/fecha={ahora:%Y-%m-%d}/hora={ahora:%H}/{context.aws_request_id}.jsonl"
    cuerpo = "\n".join(json.dumps(r, default=str) for r in registros)
    boto3.client("s3").put_object(Bucket=BUCKET_RAW, Key=clave, Body=cuerpo.encode())
    return {"registros": len(registros), "clave": clave}
