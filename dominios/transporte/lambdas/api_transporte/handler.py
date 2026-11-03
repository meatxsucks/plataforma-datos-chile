import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

TABLA = os.environ["TABLA"]
LIMITE_MAXIMO = 500
CAMPOS = ("patente", "latitud", "longitud", "velocidad", "sentido", "ruta_sinoptico", "fecha_gps")


# Respuesta HTTP en formato de integración proxy de API Gateway
def respuesta(codigo, cuerpo):
    """Arma la respuesta que espera API Gateway con cuerpo JSON; los Decimal de DynamoDB salen como número."""
    return {
        "statusCode": codigo,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(cuerpo, ensure_ascii=False, default=lambda x: float(x) if isinstance(x, Decimal) else str(x)),
    }


# Buses activos de un servicio
def buses(parametros):
    """Devuelve los buses activos del servicio (y sentido, si viene), del más reciente al más antiguo."""
    servicio = parametros.get("servicio")
    sentido = parametros.get("sentido")
    if not servicio:
        return respuesta(400, {"error": "Falta el parámetro servicio (ej. T502)"})
    if sentido not in (None, "I", "R"):
        return respuesta(400, {"error": "sentido debe ser I o R"})
    try:
        limite = min(int(parametros.get("limite", 100)), LIMITE_MAXIMO)
    except ValueError:
        return respuesta(400, {"error": "limite debe ser un entero"})

    filtro = Attr("servicio").eq(servicio)
    if sentido:
        filtro &= Attr("sentido").eq(sentido)

    # shortcut: scan con filtro sobre toda la tabla (~6.000 buses), pasar a un índice por servicio si crece
    tabla = boto3.resource("dynamodb").Table(TABLA)
    items, args = [], {"FilterExpression": filtro}
    while True:
        r = tabla.scan(**args)
        items += r["Items"]
        if "LastEvaluatedKey" not in r:
            break
        args["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    items.sort(key=lambda i: i["fecha_gps"], reverse=True)
    return respuesta(200, {
        "servicio": servicio,
        "sentido": sentido,
        "buses_activos": len(items),
        "buses": [{k: i.get(k) for k in CAMPOS} for i in items[:limite]],
    })


# Punto de entrada de la Lambda
def handler(event, context):
    """Enruta las peticiones de API Gateway a la consulta correspondiente."""
    if event.get("resource") == "/transporte/buses":
        return buses(event.get("queryStringParameters") or {})
    return respuesta(404, {"error": f"Recurso no encontrado: {event.get('resource')}"})
