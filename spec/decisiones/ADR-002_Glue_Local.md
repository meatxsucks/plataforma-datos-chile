# ADR-002 — Jobs de Glue con la imagen oficial aws-glue-libs

**Estado:** propuesta · **Fecha:** 2026-09-28

## Contexto

floci emula el catálogo de Glue pero no ejecuta jobs (`StartJobRun` no corre PySpark).

## Decisión

Los scripts de Glue se escriben como en AWS (GlueContext, DynamicFrame, job bookmarks cuando aplique) y
se ejecutan en el contenedor oficial `amazon/aws-glue-libs`, configurado para leer y escribir en el S3
de floci. Las tablas resultantes se registran en el catálogo de floci para que Athena las consulte.

Desde Airflow, un operador propio lanza el contenedor en lugar de `GlueJobOperator`.

## Alternativas

- PySpark puro sin librerías de Glue: más liviano, pero pierde lo específico de Glue (DynamicFrame, catálogo).
- Pandas o DuckDB: no practica Spark.

## Consecuencias

- La versión de la imagen fija la versión de Spark y Python; queda anotada en el README.
- Hay que confirmar en la fase 1 que la imagen corre en Apple Silicon (arm64).
