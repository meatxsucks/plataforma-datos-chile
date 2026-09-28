import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import boto3

URL_OC = "https://api.mercadopublico.cl/servicios/v1/publico/ordenesdecompra.json"
RAIZ = Path(__file__).resolve().parent.parent


# Lectura del .env
def leer_env():
    """Devuelve las variables del .env del proyecto como diccionario."""
    with open(RAIZ / ".env") as f:
        return dict(l.strip().split("=", 1) for l in f if "=" in l and not l.startswith("#"))


class LimiteExcedido(Exception):
    """La API respondió 429 de forma sostenida."""


# Consulta a la API con reintentos y respeto del 429
def consultar(params, ticket, reintentos=3, espera_429=60):
    """Consulta la API de órdenes de compra y devuelve el JSON; ante 429 espera y, si persiste, se detiene."""
    url = URL_OC + "?" + urllib.parse.urlencode({**params, "ticket": ticket})
    for intento in range(reintentos):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise RuntimeError(f"HTTP {e.code} para {params}")
            time.sleep(espera_429)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 ** intento)
    raise LimiteExcedido(f"429 persistente en {params}")


# Extracción de un día a raw
def main():
    """Descarga el detalle de las órdenes de compra de un día y lo deja tal cual en S3 raw."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fecha", required=True, help="YYYY-MM-DD")
    parser.add_argument("--bucket", default="pdc-raw")
    parser.add_argument("--pausa", type=float, default=2.0)
    parser.add_argument("--limite", type=int, default=0)
    args = parser.parse_args()

    ticket = leer_env()["MERCADOPUBLICO_TICKET"]
    fecha = datetime.strptime(args.fecha, "%Y-%m-%d")
    listado = consultar({"fecha": fecha.strftime("%d%m%Y")}, ticket)["Listado"]
    print(f"{len(listado)} órdenes en el listado del {args.fecha}")
    if args.limite:
        listado = listado[: args.limite]

    lineas, fallidas = [], []
    for i, oc in enumerate(listado, 1):
        try:
            lineas.append(json.dumps(consultar({"codigo": oc["Codigo"]}, ticket)["Listado"][0], ensure_ascii=False))
        except LimiteExcedido:
            print(f"Detenido por 429 persistente en {i}/{len(listado)}")
            break
        except (RuntimeError, IndexError, KeyError):
            fallidas.append(oc["Codigo"])
        if i % 200 == 0:
            print(f"{i}/{len(listado)}")
        time.sleep(args.pausa)

    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566"),
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    clave = f"compras/ordenes_compra/fecha_carga={args.fecha}/detalle.jsonl"
    s3.put_object(Bucket=args.bucket, Key=clave, Body="\n".join(lineas).encode("utf-8"))
    print(f"s3://{args.bucket}/{clave}: {len(lineas)} órdenes, {len(fallidas)} fallidas")


if __name__ == "__main__":
    main()
