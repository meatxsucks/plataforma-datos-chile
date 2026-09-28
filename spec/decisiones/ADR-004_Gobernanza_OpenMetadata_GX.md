# ADR-004 — Gobernanza con OpenMetadata y Great Expectations

**Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

El proyecto busca mostrar gobernanza de datos: catálogo, linaje, dueños, glosario y calidad.

## Decisión

- **OpenMetadata** como catálogo, linaje y glosario. Conectores nativos para Airflow y Postgres; MCP oficial en `https://{host}/mcp`.
- **Great Expectations** embebido en los jobs PySpark y en los DAGs (provider oficial de Airflow). No corre como servicio.
- Los resultados de calidad se publican en OpenMetadata y alimentan las tablas de monitoreo.

## Alternativas

| Opción | RAM | MCP | Motivo del descarte |
|---|---|---|---|
| DataHub | más de 7 GB, requiere Kafka y Elasticsearch | Oficial | Más pesado que OpenMetadata |
| Marquez + OpenLineage | ~4 GB | No existe | Plan B si la memoria no alcanza |
| Soda Core / Pandera | — | — | GX tiene operador oficial de Airflow y soporte Spark maduro |

## Consecuencias

- OpenMetadata pide al menos 6 GB. En un Mac de 16 GB se levanta por turnos: solo en sesiones de gobernanza, con Glue y DocumentDB apagados.
- Fuentes: docs.open-metadata.org, open-metadata.org/mcp, repositorio oficial de Great Expectations.
