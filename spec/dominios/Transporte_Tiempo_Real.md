# Transporte Santiago — tiempo real (streaming)

## Pregunta

¿Cuánto se desvía el servicio real de buses del programado, por recorrido, sentido y franja horaria?

## Fuentes

- GTFS estático de la red (recorridos, paraderos, horarios): público.
- Posiciones GPS en tiempo real: **no son públicas**; requieren gestión con el DTPM. Ver [[DUDAS]].

## Plan para el tiempo real

Mientras no haya acceso al feed real, un generador reproduce el horario del GTFS como posiciones
simuladas (con atrasos y ruido controlados) y las publica en Kinesis. El consumidor no sabe si el feed
es real o simulado: cambiar la fuente es cambiar solo el productor.

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
