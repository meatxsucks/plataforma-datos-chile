# ADR-010 — Modelo dimensional de compras públicas

**Estado:** aceptada · **Fecha:** 2026-09-28

## Decisión

Esquema estrella en Postgres (`dw`), con carga por mes desde `stage.oc_items`.

| Tabla | Grano / clave | Tipo |
|---|---|---|
| `dim_fecha` | un día (`fecha_id` AAAAMMDD), 2010–2030 | estática |
| `dim_organismo` | `codigo_organismo` | SCD 1 (MERGE) |
| `dim_unidad_compra` | `codigo_unidad` | SCD 1 (MERGE) |
| `dim_proveedor` | `codigo_proveedor` + vigencia | SCD 2 solo en `nombre_proveedor`; actividad, región y RUT en SCD 1 |
| `fact_orden_compra` | una orden (`codigo`) | montos de la orden en CLP |
| `fact_orden_compra_item` | un ítem (`id_item`) | cantidad, precio y total de línea |

## Por qué dos hechos

Los montos de la orden (`monto_total_oc_clp`) se repiten en cada ítem del archivo fuente. Dejarlos en el hecho de ítems invita a sumarlos varias veces. Cada medida vive en la tabla de su grano.

## Por qué SCD 2 solo en el nombre

La primera versión versionaba también actividad y región: agosto generó 1.205 versiones, casi todas falsas, porque esos atributos vienen por sucursal y truncados, y varían entre meses sin que el proveedor cambie. Solo la razón social es un cambio real (2 casos en tres meses).

## Vigencia

`vigente_desde` es el primer día del mes cargado, no la fecha de ejecución: permite cargar el histórico en un solo día sin vigencias invertidas. Si el nombre cambia dos veces dentro del mismo mes, se actualiza la versión de ese mes en lugar de abrir otra.

## Carga

1. Glue lee la partición de `vw_ordenes_compra_items` y sobrescribe `stage.oc_items` por JDBC.
2. Una sola transacción ejecuta `sql/bodega/02_cargar_compras.sql`: MERGE de dimensiones, SCD 2 de proveedor, DELETE del mes en los hechos e INSERT resolviendo claves sustitutas.

`MERGE` existe en Postgres 15+ y en Redshift, así que el SQL es portable (ver [[ADR-003_Postgres_Como_Bodega]]).

## Validación (2026-09-28)

Julio, agosto y septiembre cuadran con analytics en ítems, órdenes y monto en CLP; 0 duplicados, 0 huérfanos, 0 proveedores con dos versiones vigentes y 0 vigencias invertidas.
