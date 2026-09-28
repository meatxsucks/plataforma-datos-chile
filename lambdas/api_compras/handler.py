import json
import os
import re

import boto3
from pymongo import DESCENDING, MongoClient

BASE = os.environ["BASE_DOCDB"]
PATRON_MES = re.compile(r"^\d{4}-\d{2}$")
LIMITE_MAXIMO = 100

_cliente = None


# Cliente de DocumentDB reutilizado entre invocaciones
def base():
    """Devuelve la base de DocumentDB, creando el cliente la primera vez con las credenciales del secreto."""
    global _cliente
    if _cliente is None:
        secreto = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["SECRETO_DOCDB"])["SecretString"])
        _cliente = MongoClient(
            host=os.environ.get("HOST_DOCDB") or secreto["host"],
            port=int(secreto["port"]),
            username=secreto["username"],
            password=secreto["password"],
            retryWrites=False,
            serverSelectionTimeoutMS=5000,
        )
    return _cliente[BASE]


# Respuesta HTTP en formato de integración proxy de API Gateway
def respuesta(codigo, cuerpo):
    """Arma la respuesta que espera API Gateway con cuerpo JSON."""
    return {
        "statusCode": codigo,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(cuerpo, ensure_ascii=False, default=str),
    }


# Mes pedido o el último disponible
def resolver_mes(parametros):
    """Devuelve el mes del parámetro, o el último mes publicado si no viene."""
    mes = parametros.get("mes")
    if mes:
        return mes if PATRON_MES.match(mes) else None
    estado = base()["estado_api"].find_one({"_id": "resumen_organismos"}) or {}
    return max(estado.get("meses", []), default=None)


# Resumen de compras de un organismo
def resumen_organismo(codigo, mes):
    """Devuelve el documento de resumen del organismo para el mes, o 404."""
    documento = base()[f"resumen_organismos_{mes.replace('-', '_')}"].find_one({"_id": codigo})
    if not documento:
        return respuesta(404, {"error": f"Sin datos para el organismo {codigo} en {mes}"})
    documento.pop("_id")
    return respuesta(200, documento)


# Organismos con mayor concentración de proveedores
def alertas_concentracion(mes, parametros):
    """Devuelve los organismos con HHI sobre el umbral, ordenados de mayor a menor concentración."""
    try:
        umbral = int(parametros.get("hhi_min", 2500))
        limite = min(int(parametros.get("limite", 20)), LIMITE_MAXIMO)
    except ValueError:
        return respuesta(400, {"error": "hhi_min y limite deben ser enteros"})
    cursor = (
        base()[f"resumen_organismos_{mes.replace('-', '_')}"]
        .find({"hhi": {"$gte": umbral}}, {"_id": 0, "principales_proveedores": {"$slice": 1}})
        .sort([("hhi", DESCENDING), ("monto_clp", DESCENDING)])
        .limit(limite)
    )
    return respuesta(200, {"mes": mes, "hhi_min": umbral, "organismos": list(cursor)})


# Punto de entrada de la Lambda
def handler(event, context):
    """Enruta las peticiones de API Gateway a la consulta correspondiente."""
    parametros = event.get("queryStringParameters") or {}
    mes = resolver_mes(parametros)
    if not mes:
        return respuesta(400, {"error": "Parámetro mes inválido o sin meses publicados (formato AAAA-MM)"})

    recurso = event.get("resource", "")
    if recurso == "/compras/organismos/{codigo}/resumen":
        return resumen_organismo(event["pathParameters"]["codigo"], mes)
    if recurso == "/compras/alertas/concentracion":
        return alertas_concentracion(mes, parametros)
    return respuesta(404, {"error": f"Recurso no encontrado: {recurso}"})
