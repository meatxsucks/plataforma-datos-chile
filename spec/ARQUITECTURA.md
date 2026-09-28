# Arquitectura

## Vista general

```
                 ┌──────────────── BATCH ────────────────┐   ┌──────── TIEMPO REAL ────────┐
Fuentes          Mercado Público · InfoLobby · BCCh/INE      Generador/feed de posiciones
                 │                                           │
Extracción       Lambda extractora (EventBridge o DAG)       Kinesis Data Stream
                 │                                           │
                 ▼                                           ├─► Lambda consumidora ─► DynamoDB (estado actual por bus)
Raw              S3 raw/ (JSON tal cual, particionado por fecha de carga)
                 │                                           └─► S3 raw/ (micro-lotes)
Stg              Glue PySpark ─► S3 stg/ (Parquet tipado, deduplicado)
                 │
Analytics        Glue PySpark ─► S3 analytics/ + catálogo Glue ─► Athena (DuckDB en floci)
                 │
Bodega           Postgres: stage_table + DELETE/INSERT ─► modelo dimensional (dim_*, fact_*)
                 │
Gold / API       Glue INGEST ─► DocumentDB (colección por dominio y fecha)
                 │
Servicio         API Gateway (API keys + usage plans) ─► Lambda de lectura ─► DocumentDB / DynamoDB
                 │
Visualización    Streamlit sobre Postgres
Orquestación     MWAA (Airflow real en floci): DAGs por dominio con sensores de datos disponibles
Monitoreo        tablas monitor_* en Postgres + Lambda de alertas (Telegram) + explicación con OpenRouter
Gobernanza       OpenMetadata (catálogo, linaje, glosario) + Great Expectations en los jobs
Infra            Terraform con endpoints apuntando a floci
Código común     paquete Python `utils` compartido por Lambdas, Glue y DAGs
```

## Servicios y cómo se emula cada uno

Según el README de floci, revisado el 2026-09-28:

| Servicio | En floci | Uso en el proyecto |
|---|---|---|
| S3 | Emulado (versionado, multipart, notificaciones) | Capas raw, stg, analytics |
| Lambda | Real, contenedores Docker con runtime AWS | Extractores, consumidores del stream, API, alertas |
| API Gateway | REST y HTTP (v2) | Exposición de las APIs de datos |
| MWAA | Airflow real con LocalExecutor | Orquestación |
| Kinesis | Streams, shards, fan-out mejorado | Posiciones en tiempo real |
| DynamoDB | GSI, LSI, streams | Estado actual en tiempo real, API keys propias |
| EventBridge | Buses, reglas, programación | Programación de extractores |
| Step Functions | ASL | Opcional para flujos dentro de un dominio |
| DocumentDB | Real, compatible con MongoDB | Capa gold de las APIs |
| RDS Postgres | Real, en Docker | Bodega dimensional y monitoreo |
| Athena | Ejecuta SQL real con DuckDB | Consultas sobre analytics |
| Glue | **Solo catálogo y Schema Registry; no ejecuta jobs** | Ver [[ADR-002_Glue_Local]] |
| Redshift | **Solo control plane; no ejecuta SQL** | Ver [[ADR-003_Postgres_Como_Bodega]] |

## Capas y contratos

| Capa | Formato | Regla |
|---|---|---|
| raw | JSON/CSV tal como llega | Inmutable. Partición `dominio/entidad/fecha_carga=YYYY-MM-DD/` |
| stg | Parquet | Tipos correctos, nombres normalizados, deduplicado por clave natural |
| analytics | Parquet + tabla en catálogo | Modelado para consulta; se registra en el catálogo Glue |
| bodega | Postgres | Dimensiones con clave sustituta; hechos con grano explícito |
| gold | DocumentDB | Documento listo para servir; una colección por entidad y fecha de corte |

## Decisiones

- [[ADR-001_Floci_Como_Emulador]]
- [[ADR-002_Glue_Local]]
- [[ADR-003_Postgres_Como_Bodega]]
- [[ADR-004_Gobernanza_OpenMetadata_GX]]
- [[ADR-005_IA_Monitoreo_OpenRouter]]
- [[ADR-006_MCP_Por_Servicio]]
- [[ADR-007_Diagramas_Como_Codigo]]
- [[ADR-008_Proteccion_Datos_Personales]]
- [[ADR-009_Extraccion_Archivo_Masivo]]
