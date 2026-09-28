# Patrón de jobs de Glue

Estructura común a todos los jobs del proyecto, inspirada en prácticas habituales de equipos de datos en AWS.

## Esqueleto

1. Un script por job; el archivo se llama igual que el job.
2. Parámetros con `getResolvedOptions`: `JOB_NAME`, `fechaParticion`, buckets de origen y destino, base del catálogo. Nada de rutas en duro.
3. `job.init` → lectura a DynamicFrame → vistas temporales → transformación en Spark SQL (`spark_sql` de `utils`).
4. `purgar_particion` antes de escribir: reejecutar no duplica.
5. Escritura Parquet snappy particionada por fecha, con `repartition` por la clave para evitar archivos chicos.
6. `registrar_tabla` en el catálogo y `job.commit`.

## Familias por capa

| Familia | Qué hace |
|---|---|
| `pdc_vw_*` | raw/stg → analytics + catálogo |
| `pdc_cert_*` | analytics → certificado (purga y reescritura) |
| `pdc_dim_*` | certificado → bodega (stage + DELETE/INSERT) |
| `pdc_api_*` | bodega → S3 capa API |
| `pdc_api_*_ingest` | S3 API → DocumentDB, colección `{NOMBRE}_{fecha}` |

## Lecciones

- Sin `repartition`, un `ROW_NUMBER` deja 200 particiones de shuffle y escribe decenas de archivos chicos (50 archivos para 60 filas en la primera prueba).
- En local, Glue usa su propio catálogo; `registrar_tabla` escribe la tabla en el catálogo de floci vía boto3.
- `s3://` se mapea a S3A con endpoint de floci en `scripts/glue_local.sh`.
- El lector CSV de DynamicFrame no maneja latin-1 ni campos multilínea: los archivos masivos se leen con `spark.read.csv` y se vuelve a DynamicFrame para escribir.
- `SELECT * EXCEPT` no existe en Spark 3.5 (Glue 5): la lista de columnas se arma en Python.
