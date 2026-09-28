# ADR-012 — API de datos de compras: bodega → S3 → DocumentDB → API Gateway

**Estado:** aceptada · **Fecha:** 2026-09-28

## Decisión

| Paso | Componente | Detalle |
|---|---|---|
| 1 | `pdc_api_resumen_organismos` | Consulta la bodega (`sql/api/resumen_organismos.sql`) y escribe en `s3://pdc-api/resumen_organismos/mes=AAAA-MM/` un documento por organismo con los 5 principales proveedores anidados |
| 2 | `pdc_api_resumen_organismos_ingest` | Carga los documentos en una colección temporal de DocumentDB, valida el conteo y la renombra sobre `resumen_organismos_AAAA_MM` (`renameCollection` con `dropTarget`, atómico). Registra el mes en `estado_api` |
| 3 | Lambda `pdc-api-compras` | Lee DocumentDB con el secreto `pdc/docdb`; cliente reutilizado entre invocaciones |
| 4 | API Gateway REST `pdc-api-compras`, etapa `v1` | Integración proxy con la Lambda; API key obligatoria; plan de uso de 10 req/s (ráfaga 20) y 1.000 req/día |

## Endpoints

- `GET /compras/organismos/{codigo}/resumen?mes=AAAA-MM` — monto, órdenes, proveedores, % trato directo, % compra ágil, HHI y principales proveedores. Sin `mes`, usa el último publicado.
- `GET /compras/alertas/concentracion?mes&hhi_min=2500&limite=20` — organismos con mayor concentración.

## Indicador de concentración

HHI = Σ (participación % de cada proveedor en el monto del organismo)². 10.000 es un solo proveedor; bajo 1.500 se considera baja concentración y sobre 2.500, alta.

## Por qué colección por mes y renombre

Replica el patrón de colección por fecha de corte: publicar un mes nuevo o recargarlo no toca los demás, y el renombre atómico evita que la API lea una carga a medias.

## Limitaciones de floci encontradas

- El provider de Terraform falla al leer la API key que crea floci (no devuelve fechas): la key se crea con `scripts/crear_api_key.sh`.
- floci no devuelve `timeoutInMillis` de la integración y rechaza actualizarlo: `ignore_changes` en Terraform.
- La imagen de Glue no trae `pymongo`: el emulador soporta `--additional-python-modules`, como Glue real.

## Validación (2026-09-28)

Con API key: 200 con datos; sin key o con key falsa: 403; organismo inexistente: 404; mes inválido: 400.
