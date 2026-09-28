# Compras públicas — dominio principal (batch)

## Pregunta

¿Qué organismos del Estado concentran sus compras en pocos proveedores o en trato directo, cómo
evoluciona eso en el tiempo, y coincide con audiencias de lobby de esos mismos proveedores?

## Fuentes

- Mercado Público (ChileCompra): licitaciones y órdenes de compra. Ver [[Fuentes_de_Datos]].
- InfoLobby: audiencias, viajes y donativos (descargas de datos abiertos y SPARQL).

## Flujo

1. Lambda extractora diaria (09:00): archivo masivo del mes en curso → `raw/compras/ordenes_compra_masiva/mes=AAAA-MM/`. Ver [[ADR-009_Extraccion_Archivo_Masivo]].
2. Carga histórica: la misma Lambda con `{"meses": ["2026-07", ...]}`.
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

## Primeros resultados (julio y agosto 2026)

| Mes | Ítems | Órdenes | % ítems en trato directo | % del monto en trato directo |
|---|---|---|---|---|
| 2026-07 | 427.834 | 151.130 | 4,5 | 19,7 |
| 2026-08 | 433.800 | 153.553 | 4,3 | 15,1 |

El trato directo es una fracción chica de las compras, pero concentra entre 15% y 20% del monto: son pocas compras grandes. El monto se mide con `monto_total_oc_clp` a nivel de orden, porque las líneas pueden venir en UF.
