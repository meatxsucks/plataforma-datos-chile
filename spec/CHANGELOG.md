# CHANGELOG

## 2026-09-28

- Creado el proyecto `plataforma-datos-chile` con el vault `spec/`: README, AGENTS,
  ARQUITECTURA, TODO, DUDAS, notas de los tres dominios, fuentes de datos, ADR-001 a ADR-003 y patrones.
- DUDAS 1 y 3 resueltas: el repo se mantiene en OneDrive y la visualización será Streamlit; actualizadas ARQUITECTURA y Economia_Regional.
- DUDAS 6 resuelta: OpenMetadata como catálogo, metadata y linaje.
- Agregados ADR-004 (OpenMetadata + Great Expectations), ADR-005 (OpenRouter para alertas), ADR-006 (MCP por servicio) y ADR-007 (diagramas como código); actualizados ARQUITECTURA y TODO (fase 6b de gobernanza, tareas de MCP y diagrama en fase 1).
- Docker Desktop levantado (29.0.1, ~7,6 GB) y Graphviz confirmado (15.1); DUDAS 4 resuelta. Documentado en Fuentes_de_Datos el trámite del DTPM para posiciones GPS.
- Creados .gitignore (excluye .env), .env.example y .env con MERCADOPUBLICO_TICKET vacío.
- Ticket de Mercado Público guardado en .env y probado: HTTP 200, 1.316 órdenes de compra del 26-09-2026. Solicitud de posiciones GPS enviada al DTPM.
- Fase 1a: docker-compose.yml (floci, persistencia hybrid), Terraform (providers.tf, base.tf: bucket pdc-raw, rol y Lambda pdc-hola) y lambdas/hola/handler.py; .gitignore ampliado.
- Fase 1a probada: floci 2.1.0 arriba; terraform apply creó pdc-raw, pdc-lambda-rol y pdc-hola; la invocación devolvió {"ok": true, "bucket_raw": "pdc-raw"}; bucket y Lambda persisten tras reiniciar el contenedor.
- Fase 1b: Terraform agrega buckets pdc-stg, pdc-analytics, pdc-cert, pdc-sensible y pdc-athena-resultados, y la base pdc del catálogo; endpoints glue y athena en el provider.
- `scripts/extraer_ordenes_dia.py`: extracción de un día a raw. Primera corrida detenida por 429 de la API; se agregó pausa de 2 s, espera de 60 s ante 429, corte ante 429 persistente y `--limite`. Muestra de 60 órdenes cargada sin fallas.
- `utils/glue_utils.py` (spark_sql, purgar_particion, registrar_tabla), `glue/jobs/pdc_vw_ordenes_compra.py` y `scripts/glue_local.sh` (imagen Glue 5 arm64 contra floci).
- Seudonimización de proveedores persona natural y diccionario separado en pdc-sensible (ADR-008); CLAVE_SEUDONIMO agregada a .env.
- Job probado: 60 leídos, 60 escritos, 3 personas naturales en el diccionario; tabla y partición registradas en el catálogo de floci. Detectados 50 archivos para 60 filas: se agrega repartition por fecha.
- Athena de floci falló al descargar floci/floci-duck: Docker no alcanzaba Docker Hub por un problema de red local. Pendiente reintentar.
- Notas nuevas: ADR-008_Proteccion_Datos_Personales y aprendizaje/Patron_Jobs_Glue; Fuentes_de_Datos actualizado con el 429 y las descargas masivas.
- Docker Desktop reiniciado a la fuerza tras quedar colgado por un cambio de red; floci conservó buckets y catálogo. Descargada floci/floci-duck.
- Fase 1b verificada con Athena: 60 filas, 60 códigos, monto 194.722.172, 3 personas naturales con nombre enmascarado y token de 64 caracteres; la reejecución no duplica y escribe 1 archivo tras el repartition.
- Fase 1c: diagrama `docs/diagramas/arquitectura_general.py` (PNG y SVG, íconos oficiales AWS); README raíz; requirements-dev con boto3 y diagrams.
- `uv` instalado con Homebrew. `aws-api-mcp-server` probado contra floci con `scripts/probar_mcp_aws.py`: lista S3 y el catálogo de Glue; escritura bloqueada con READ_OPERATIONS_ONLY. Configurado en `.mcp.json`. ADR-006 actualizado.
- Datos de floci movidos fuera de OneDrive a `~/.pdc/floci-data` (docker-compose apunta a `${HOME}/.pdc/floci-data`); catálogo conservado.
- Backfill julio y agosto 2026 desde archivos masivos de ChileCompra a `s3://pdc-raw/compras/ordenes_compra_masiva/mes=AAAA-MM/`. Nuevo job `pdc_vw_ordenes_compra_items` (grano ítem, seudonimización, diccionario en pdc-sensible): 427.834 y 433.800 ítems, ~1:40 min por mes con 4 GB de driver.
- `utils/glue_utils.py`: `sql_es_persona_natural`, `sql_token_rut` y `sql_decimal`; el job de órdenes los reutiliza. `glue_local.sh` acepta `MEMORIA_DRIVER`.
- Diagrama rehecho con líneas ortogonales y fronteras AWS Cloud, cuenta y región us-east-1.
- Primer hallazgo en Compras_Publicas: el trato directo es ~4% de los ítems pero 15–20% del monto.
- Fase 2: Lambda `pdc-extractor-oc-masiva` (descarga el zip mensual y lo descomprime en streaming a raw, idempotente por ETag) y EventBridge Scheduler `pdc-extractor-oc-masiva-diario` (cron 09:00 America/Santiago) en `infra/terraform/extraccion.tf`; endpoints scheduler y logs en el provider.
- Probado: invocación manual cargó septiembre (601 MB) en ~30 s; segunda invocación devolvió `sin_cambios`; un schedule puntual `at()` disparó la Lambda en floci (se borró tras la prueba).
- Septiembre procesado con `pdc_vw_ordenes_compra_items`: 355.585 ítems, 6.003 personas naturales en el diccionario. Verificado que ningún ítem se repite entre meses. ADR-009.
- Fase 3: RDS Postgres 16 (`pdc-bodega`) y secreto `pdc/bodega` en Secrets Manager (`infra/terraform/bodega.tf`); proxy de floci expuesto en `localhost:7001`. POSTGRES_PASSWORD en .env, pasado a Terraform como TF_VAR.
- `sql/bodega/01_ddl.sql` (esquemas stage y dw, dimensiones y dos hechos) y `02_cargar_compras.sql` (MERGE, SCD 2 de proveedor, DELETE/INSERT por mes). Job `pdc_dim_compras`; `utils` suma `obtener_secreto`, `url_jdbc`, `ejecutar_sql` y `leer_sentencias`.
- Primera carga generó ~1.200 versiones falsas de proveedor por mes (actividad y región varían por sucursal) y vigencias invertidas (fecha de carga); corregido: SCD 2 solo en nombre, vigencia desde el primer día del mes. Bodega truncada y recargada.
- Validación: julio, agosto y septiembre cuadran con Athena en ítems, órdenes y monto CLP; 0 duplicados, 0 huérfanos, 0 vigencias inconsistentes. ADR-010.
- MCP de Postgres (`postgres-mcp`, modo restricted, rol `pdc_lector` con `03_rol_lector.sql`) probado: consulta sí, DELETE rechazado. Requiere `--with mcp<2`.
- Fase 4: emulador `emuladores/glue_jobs` (servicio `glue-jobs` en docker-compose) que ejecuta `StartJobRun` con el contenedor de Glue y reenvía el resto a floci. ADR-011.
- Terraform: `glue_jobs.tf` (bucket pdc-glue-assets con jobs, utils y SQL; secreto pdc/seudonimo; jobs pdc_vw_ordenes_compra_items y pdc_dim_compras) y `orquestacion.tf` (VPC, subredes privadas, security group, bucket pdc-mwaa con DAGs, MWAA pdc-airflow 2.10.5 con SecretsManagerBackend y secreto airflow/connections/aws_default).
- Jobs leen la clave de seudonimización desde Secrets Manager (`--secretoSeudonimo`) y el SQL desde S3; ADR-008 actualizado.
- `airflow/dags/dag_compras_diario.py` probado: corrida manual y programada en success (ítems 1:38, bodega 0:43), conteos de la bodega sin cambios.
- Reiniciar floci deja huérfanos los contenedores de MWAA y mueve el puerto del proxy web: `scripts/recrear_mwaa.sh` limpia y recrea; servicio `airflow-ui` (socat) publica la interfaz en `localhost:8080`.
