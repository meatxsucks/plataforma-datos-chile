# ADR-006 — MCP por servicio

**Estado:** propuesta · **Fecha:** 2026-09-28

## Contexto

Se quiere operar el stack desde agentes vía MCP. Investigación del 2026-09-28; "verificado" significa que se vio en el README del proyecto.

## Servidores elegidos

| Servicio | Servidor | Licencia | Apunta al entorno local | Estado |
|---|---|---|---|---|
| S3, Lambda, DynamoDB, Kinesis, API Gateway | `aws-api-mcp-server` (awslabs/mcp) | Apache-2.0 | **Verificado 2026-09-28:** respeta `AWS_ENDPOINT_URL`; lista S3 y lee el catálogo de Glue de floci | Adoptado en `.mcp.json`, solo lectura |
| Glue catálogo + Athena | `aws-dataprocessing-mcp-server` (awslabs/mcp) | Apache-2.0 | No confirmado, mismo caso | Probar en fase 2 |
| Postgres | `crystaldba/postgres-mcp` | MIT | Verificado: `DATABASE_URI` | Adoptar |
| DocumentDB (Mongo local) | `mongodb-js/mongodb-mcp-server` (oficial MongoDB) | Apache-2.0 | Verificado: `MDB_MCP_CONNECTION_STRING` acepta instancia local | Adoptar |
| OpenMetadata | MCP oficial `https://{host}/mcp` | — | Verificado en docs | Adoptar en fase de gobernanza |
| OpenRouter | MCP oficial `https://mcp.openrouter.ai/mcp` | — | Verificado en docs | Opcional |
| Diagramas | `jgraph/drawio-mcp` | Apache-2.0 | Local | Opcional, ver [[ADR-007_Diagramas_Como_Codigo]] |
| Airflow | `abhishekbhakat/airflow-mcp-server` | MIT | Verificado: `--base-url` | En evaluación: sin commits desde oct-2025 |
| Docker | `ckreiling/mcp-server-docker` | GPL-3.0 | Verificado | En evaluación |
| Terraform | `hashicorp/terraform-mcp-server` | MPL-2.0 | Orientado a HCP Terraform, no a ejecutar local | Solo consulta de providers y módulos |
| Streamlit | No existe MCP relevante | — | — | No aplica |

## Descartados

- `documentdb-mcp-server` de awslabs: asume TLS contra un clúster real de AWS; para Mongo local sirve más el oficial de MongoDB.

## Consecuencias

- Si los MCP de awslabs no respetan el endpoint de floci, el plan B es la CLI `aws` con `AWS_ENDPOINT_URL` desde Bash.

## Modo solo lectura

El MCP de AWS corre con `READ_OPERATIONS_ONLY=true`: consulta, pero no crea ni borra (probado: `aws s3 mb` fue rechazado por la política). Los cambios de infraestructura pasan por Terraform, que deja registro y se puede revisar antes de aplicar.
