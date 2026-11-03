"""Genera una página Leaflet con los buses activos que hay en DynamoDB.

Uso: .venv/bin/python dominios/transporte/scripts/mapa_buses.py [salida.html]
"""
import json
import sys
from pathlib import Path

import boto3

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/capturas/mapa_buses.html")

PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Buses activos - Santiago</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<style>html,body,#mapa{height:100%;margin:0}#leyenda{position:absolute;z-index:1000;right:10px;top:10px;background:#fff;padding:8px 12px;font:13px sans-serif;border-radius:6px;box-shadow:0 1px 4px #0005}
i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}</style></head>
<body><div id="mapa"></div>
<div id="leyenda"><b>__TOTAL__ buses activos</b> (GPS de menos de 5 min)<br>
<i style="background:#888"></i>detenido<br><i style="background:#f59e0b"></i>menos de 20 km/h<br><i style="background:#16a34a"></i>20 km/h o más</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script>
const buses = __DATOS__;
const mapa = L.map("mapa").setView([-33.45, -70.66], 11);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 18, attribution: "OpenStreetMap"}).addTo(mapa);
for (const b of buses) {
  const color = b.v === 0 ? "#888" : b.v < 20 ? "#f59e0b" : "#16a34a";
  L.circleMarker([b.la, b.lo], {radius: 3, color, weight: 1, fillOpacity: 0.8})
    .bindPopup(`${b.p}<br>${b.s} ${b.d}<br>${b.v} km/h`).addTo(mapa);
}
</script></body></html>
"""


def main():
    tabla = boto3.resource("dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1",
                           aws_access_key_id="test", aws_secret_access_key="test").Table("pdc-buses-actuales")
    items, args = [], {}
    while True:
        r = tabla.scan(**args)
        items += r["Items"]
        if "LastEvaluatedKey" not in r:
            break
        args["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    buses = [{"p": i["patente"], "la": float(i["latitud"]), "lo": float(i["longitud"]), "v": float(i["velocidad"]),
              "s": i["servicio"], "d": i["sentido"]} for i in items]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(PAGINA.replace("__DATOS__", json.dumps(buses)).replace("__TOTAL__", str(len(buses))))
    print(f"{len(buses)} buses en {SALIDA}")


if __name__ == "__main__":
    main()
