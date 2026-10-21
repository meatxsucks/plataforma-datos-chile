# Transporte Santiago — tiempo real (streaming)

## Pregunta

¿Cuánto se desvía el servicio real de buses del programado, por recorrido, sentido y franja horaria?

## Fuentes

- GTFS estático de la red (recorridos, paraderos, horarios): público.
- Posiciones GPS y alertas en tiempo real del DTPM: **acceso otorgado el 2026-10-21**. Ver [[DTPM_Web_Services]].
- Diccionario de servicios (archivo DECO) para traducir el código interno al recorrido público.

## Plan para el tiempo real

Un productor consulta el servicio de posiciones del DTPM cada 1 minuto (el mínimo permitido) y publica cada bus en Kinesis. El simulador desde GTFS queda solo como respaldo para pruebas sin conexión.

## Flujo

1. Carga batch del GTFS estático → raw → stg → bodega (`dim_recorrido`, `dim_paradero`, `dim_horario`).
2. Productor → Kinesis (`posiciones`), un registro por bus cada N segundos.
3. Lambda consumidora:
   - actualiza DynamoDB con la última posición por bus (estado actual);
   - escribe micro-lotes a `raw/transporte/posiciones/`.
4. Glue cada hora: compara posiciones contra el horario programado → `fact_puntualidad`.
5. API: `GET /transporte/recorridos/{id}/buses` (desde DynamoDB) y `GET /transporte/recorridos/{id}/puntualidad`.

## Conceptos que se practican

- Particionado por clave en Kinesis (por patente o recorrido) y orden dentro del shard.
- Idempotencia del consumidor ante reintentos.
- Ventanas temporales y datos que llegan tarde.
- Separación entre estado actual (DynamoDB) e historia (S3/bodega).
