import json
import os
import urllib.request
from datetime import datetime, timezone

import boto3
import pg8000.native

BUCKET_RAW = os.environ["BUCKET_RAW"]
PREFIJO_RAW = "compras/ordenes_compra_masiva"
HORAS_MAXIMAS_RAW = 36
CAIDA_MAXIMA = 0.10

_conexion = None


# Conexión a la bodega reutilizada entre invocaciones
def bodega():
    """Abre la conexión a Postgres con las credenciales del secreto la primera vez."""
    global _conexion
    if _conexion is None:
        secreto = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["SECRETO_BODEGA"])["SecretString"])
        _conexion = pg8000.native.Connection(
            user=secreto["username"],
            password=secreto["password"],
            host=os.environ.get("HOST_BODEGA") or secreto["host"],
            port=int(secreto["port"]),
            database=secreto["dbname"],
            timeout=10,
        )
    return _conexion


# Chequeo de frescura del archivo mensual en raw
def frescura_raw(mes):
    """Falla si el CSV del mes no existe o tiene más de 36 horas."""
    anio, numero = mes.split("-")
    clave = f"{PREFIJO_RAW}/mes={mes}/{anio}-{int(numero)}.csv"
    try:
        modificado = boto3.client("s3").head_object(Bucket=BUCKET_RAW, Key=clave)["LastModified"]
    except Exception:
        return "falla", None, f"<= {HORAS_MAXIMAS_RAW} h", f"No existe s3://{BUCKET_RAW}/{clave}"
    horas = (datetime.now(timezone.utc) - modificado).total_seconds() / 3600
    estado = "ok" if horas <= HORAS_MAXIMAS_RAW else "falla"
    return estado, round(horas, 1), f"<= {HORAS_MAXIMAS_RAW} h", f"Archivo cargado hace {horas:.1f} h"


# Chequeo de volumen de ítems contra la última medición
def volumen_items(mes):
    """Falla si los ítems del mes caen más de un 10% respecto de la medición anterior."""
    actual = bodega().run("SELECT count(*) FROM dw.fact_orden_compra_item WHERE mes = :mes", mes=mes)[0][0]
    previo = bodega().run(
        "SELECT valor FROM monitoreo.chequeos WHERE chequeo = 'volumen_items' AND mes = :mes ORDER BY ejecutado_en DESC LIMIT 1",
        mes=mes,
    )
    if actual == 0:
        return "falla", actual, "> 0", "El mes no tiene ítems en la bodega"
    if previo and actual < float(previo[0][0]) * (1 - CAIDA_MAXIMA):
        return "falla", actual, f">= {float(previo[0][0]) * (1 - CAIDA_MAXIMA):.0f}", f"Antes {float(previo[0][0]):.0f} ítems, ahora {actual}"
    return "ok", actual, "sin caída > 10%", f"{actual} ítems"


# Chequeo de integridad entre hechos
def items_sin_ordenes(mes):
    """Falla si hay ítems en el mes pero ninguna orden de compra."""
    ordenes = bodega().run("SELECT count(*) FROM dw.fact_orden_compra WHERE mes = :mes", mes=mes)[0][0]
    items = bodega().run("SELECT count(*) FROM dw.fact_orden_compra_item WHERE mes = :mes", mes=mes)[0][0]
    estado = "falla" if items > 0 and ordenes == 0 else "ok"
    return estado, ordenes, "> 0 si hay ítems", f"{ordenes} órdenes y {items} ítems"


CHEQUEOS = {"frescura_raw": frescura_raw, "volumen_items": volumen_items, "items_sin_ordenes": items_sin_ordenes}


# Explicación opcional de la falla con un modelo de OpenRouter
def explicar(chequeo, mes, detalle):
    """Pide al modelo una hipótesis de causa; devuelve None si no hay clave o la consulta falla."""
    clave = os.environ.get("OPENROUTER_API_KEY")
    if not clave:
        return None
    pedido = {
        "model": os.environ["OPENROUTER_MODELO"],
        "max_tokens": 200,
        "messages": [{
            "role": "user",
            "content": f"Un chequeo de calidad de una bodega de compras públicas falló. Chequeo: {chequeo}. Mes: {mes}. "
                       f"Detalle: {detalle}. En 3 frases en español: causa más probable y qué revisar primero.",
        }],
    }
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(pedido).encode(),
            headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


# Punto de entrada: corre los chequeos del mes y registra alertas
def handler(event, context):
    """Ejecuta los chequeos, guarda cada resultado y crea una alerta por cada falla."""
    mes = (event or {}).get("mes") or datetime.now(timezone.utc).strftime("%Y-%m")
    resultados = []
    for nombre, funcion in CHEQUEOS.items():
        estado, valor, esperado, detalle = funcion(mes)
        chequeo_id = bodega().run(
            "INSERT INTO monitoreo.chequeos (chequeo, mes, estado, valor, esperado, detalle) "
            "VALUES (:c, :m, :e, :v, :x, :d) RETURNING chequeo_id",
            c=nombre, m=mes, e=estado, v=valor, x=esperado, d=detalle,
        )[0][0]
        if estado == "falla":
            bodega().run(
                "INSERT INTO monitoreo.alertas (chequeo_id, mensaje, explicacion) VALUES (:i, :m, :x)",
                i=chequeo_id, m=f"{nombre} {mes}: {detalle}", x=explicar(nombre, mes, detalle),
            )
        resultados.append({"chequeo": nombre, "estado": estado, "detalle": detalle})
    return {"mes": mes, "resultados": resultados}
