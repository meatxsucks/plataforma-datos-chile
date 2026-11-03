import base64
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3

STREAM = os.environ["STREAM"]
URL = "http://www.dtpmetropolitano.cl/posiciones"
MINUTOS_ACTIVO = 5
LOTE_KINESIS = 500
CAMPOS = [
    "fecha_gps", "patente", "latitud", "longitud", "velocidad", "direccion",
    "operador", "servicio", "sentido", "ruta_consola", "ruta_sinoptico", "fecha_insercion",
]


# Consulta de posiciones al DTPM
def consultar():
    """Pide las posiciones con HTTP Basic y devuelve el JSON; falla con el mensaje del servicio si no trae posiciones."""
    secreto = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["SECRETO_DTPM"])["SecretString"])
    token = base64.b64encode(f"{secreto['usuario']}:{secreto['clave']}".encode()).decode()
    req = urllib.request.Request(URL, headers={"Authorization": f"Basic {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = json.load(r)
    if "posiciones" not in datos:
        raise RuntimeError(f"Respuesta sin posiciones: {str(datos)[:300]}")
    return datos


# Última transmisión de cada bus activo
def activos(datos, ahora):
    """Devuelve un registro por bus cuya última transmisión GPS (UTC) tiene menos de 5 minutos."""
    limite = ahora - timedelta(minutes=MINUTOS_ACTIVO)
    registros = []
    for texto in datos["posiciones"]:
        c = texto.split(";")[:12]
        if len(c) < 12:
            continue
        try:
            gps = datetime.strptime(c[0], "%d-%m-%Y %H:%M:%S").replace(tzinfo=timezone.utc)
            if gps < limite:
                continue
            r = dict(zip(CAMPOS, c))
            r["fecha_gps"] = gps.isoformat()
            for campo in ("latitud", "longitud", "velocidad"):
                r[campo] = float(r[campo])
        except ValueError:
            continue
        r["consulta"] = datos["fecha_consulta"]
        registros.append(r)
    return registros


# Publicación en Kinesis por lotes
def publicar(registros):
    """Envía los registros a Kinesis con la patente como clave de partición y devuelve cuántos fallaron."""
    kinesis = boto3.client("kinesis")
    fallidos = 0
    for i in range(0, len(registros), LOTE_KINESIS):
        lote = [{"Data": json.dumps(r).encode(), "PartitionKey": r["patente"]} for r in registros[i:i + LOTE_KINESIS]]
        fallidos += kinesis.put_records(StreamName=STREAM, Records=lote)["FailedRecordCount"]
    return fallidos


# Punto de entrada: una consulta por invocación
def handler(event, context):
    """Consulta posiciones, filtra los buses activos y los publica en el stream."""
    datos = consultar()
    registros = activos(datos, datetime.now(timezone.utc))
    fallidos = publicar(registros)
    return {"buses_respuesta": len(datos["posiciones"]), "buses_activos": len(registros), "fallidos": fallidos}
