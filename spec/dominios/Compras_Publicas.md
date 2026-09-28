# Compras públicas — dominio principal (batch)

## Pregunta

¿Qué organismos del Estado concentran sus compras en pocos proveedores o en trato directo, cómo
evoluciona eso en el tiempo, y coincide con audiencias de lobby de esos mismos proveedores?

## Fuentes

- Mercado Público (ChileCompra): licitaciones y órdenes de compra. Ver [[Fuentes_de_Datos]].
- InfoLobby: audiencias, viajes y donativos (descargas de datos abiertos y SPARQL).

## Flujo

1. Lambda extractora diaria: órdenes de compra y licitaciones del día anterior → `raw/compras/...`.
   Pagina por fecha, respeta el límite diario del ticket y guarda la respuesta tal cual.
2. Carga histórica (backfill): un DAG que recorre fechas hacia atrás, en horario valle.
3. Glue stg: aplanar JSON, tipar montos y fechas, normalizar RUT, deduplicar por código.
4. Glue analytics: hechos y dimensiones en Parquet, registrados en el catálogo.
5. Carga a la bodega: `stage_table` + DELETE/INSERT por fecha.
6. INGEST a DocumentDB y API de lectura.

## Modelo dimensional (borrador)

- `dim_organismo` (código, nombre, sector, región)
- `dim_proveedor` (RUT normalizado, razón social) — SCD tipo 2 si cambia la razón social
- `dim_fecha`
- `dim_tipo_compra` (licitación, trato directo, convenio marco, compra ágil)
- `fact_orden_compra` — grano: una línea de orden de compra
- `fact_licitacion` — grano: una licitación con su estado final
- `fact_audiencia_lobby` — grano: una audiencia

## Transformaciones interesantes

- Índice de concentración Herfindahl-Hirschman (HHI) por organismo y trimestre.
- Proporción de trato directo sobre el monto total.
- Resolución de entidades entre lobby y compras: los nombres de empresas y organismos no comparten clave; hay que normalizar y hacer coincidencia aproximada, con una tabla de equivalencias revisable.

## API

- `GET /compras/organismos/{codigo}/resumen?desde&hasta`
- `GET /compras/proveedores/{rut}/ordenes?desde&hasta`
- `GET /compras/alertas/concentracion?trimestre`
