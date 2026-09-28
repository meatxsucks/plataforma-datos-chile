# ADR-009 — Extracción diaria desde el archivo masivo y no desde la API

**Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

La API de Mercado Público entrega, por fecha, solo código, nombre y estado; el detalle exige una consulta por orden (~1.300 al día). A ritmo seguro (2 s entre consultas, para no recibir 429) son ~45 minutos, más que el máximo de 15 minutos de una Lambda, y consume ~13% del límite diario del ticket.

ChileCompra publica además un archivo por mes (`oc-da/{AAAA}-{M}.zip`) con todas las órdenes a nivel de ítem, y el del mes en curso se actualiza a diario.

## Decisión

- Lambda `pdc-extractor-oc-masiva`, disparada por EventBridge Scheduler todos los días a las 09:00 (America/Santiago).
- Descarga el zip del mes en curso y, los primeros 5 días del mes, también el del mes anterior para capturar cambios tardíos.
- Descomprime en streaming directo a `s3://pdc-raw/compras/ordenes_compra_masiva/mes=AAAA-MM/`, guardando en la metadata el ETag de origen.
- Si el ETag no cambió desde la última carga, no hace nada (idempotente).
- La API queda para consultas puntuales de detalle (`scripts/extraer_ordenes_dia.py`).

## Alternativas

| Opción | Motivo del descarte |
|---|---|
| API orden por orden en una Lambda | Supera los 15 minutos y arriesga 429 y suspensión del ticket |
| API con fan-out por SQS a varias Lambdas | Más rápido, pero multiplica la presión sobre el límite de la API; innecesario si existe el archivo |

## Consecuencias

- Una ejecución tarda ~30 s localmente y usa 1 GB de memoria y 1 GB de disco efímero.
- Cada ítem aparece en un solo archivo mensual (verificado: 0 ítems repetidos entre julio, agosto y septiembre), así que los meses se suman sin duplicar.
- Dependencia de la URL del blob de ChileCompra: si cambia, falla la descarga y debe alertar el monitoreo.
