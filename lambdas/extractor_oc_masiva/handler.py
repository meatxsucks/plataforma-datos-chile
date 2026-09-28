import os
import shutil
import urllib.request
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import boto3

URL_BASE = "https://transparenciachc.blob.core.windows.net/oc-da"
PREFIJO_RAW = "compras/ordenes_compra_masiva"
DIAS_MES_ANTERIOR = 5

s3 = boto3.client("s3")


# Meses que corresponde cargar en la fecha dada
def meses_a_cargar(hoy):
    """Devuelve el mes en curso y, en los primeros días del mes, también el anterior."""
    meses = [(hoy.year, hoy.month)]
    if hoy.day <= DIAS_MES_ANTERIOR:
        meses.insert(0, (hoy.year - 1, 12) if hoy.month == 1 else (hoy.year, hoy.month - 1))
    return meses


# ETag del archivo ya cargado en raw
def etag_cargado(bucket, clave):
    """Devuelve el ETag de origen guardado en la metadata del objeto raw, o None si no existe."""
    try:
        return s3.head_object(Bucket=bucket, Key=clave)["Metadata"].get("origen-etag")
    except s3.exceptions.ClientError:
        return None


# Carga de un mes desde el archivo masivo a raw
def cargar_mes(bucket, anio, mes):
    """Descarga el zip del mes y sube el CSV a raw tal cual, salvo que no haya cambiado desde la última carga."""
    url = f"{URL_BASE}/{anio}-{mes}.zip"
    clave = f"{PREFIJO_RAW}/mes={anio}-{mes:02d}/{anio}-{mes}.csv"

    cabecera = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60)
    etag = cabecera.headers["ETag"].strip('"')
    if etag_cargado(bucket, clave) == etag:
        return {"mes": f"{anio}-{mes:02d}", "estado": "sin_cambios"}

    ruta_zip = f"/tmp/{anio}-{mes}.zip"
    with urllib.request.urlopen(url, timeout=300) as r, open(ruta_zip, "wb") as f:
        shutil.copyfileobj(r, f)

    with zipfile.ZipFile(ruta_zip) as z:
        miembro = z.infolist()[0]
        with z.open(miembro) as csv:
            s3.upload_fileobj(
                csv,
                bucket,
                clave,
                ExtraArgs={"Metadata": {"origen-etag": etag, "origen-url": url, "cargado": datetime.utcnow().isoformat()}},
            )
    os.remove(ruta_zip)
    return {"mes": f"{anio}-{mes:02d}", "estado": "cargado", "bytes": miembro.file_size}


# Punto de entrada de la Lambda
def handler(event, context):
    """Carga a raw los archivos masivos de órdenes de compra del mes en curso y, si aplica, del anterior."""
    bucket = os.environ["BUCKET_RAW"]
    if event.get("meses"):
        meses = [tuple(int(x) for x in m.split("-")) for m in event["meses"]]
    else:
        meses = meses_a_cargar(datetime.now(ZoneInfo("America/Santiago")).date())
    return {"resultados": [cargar_mes(bucket, anio, mes) for anio, mes in meses]}
