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
- Fase 5: DocumentDB `pdc-docdb` y secreto `pdc/docdb` (`infra/terraform/api.tf`); jobs `pdc_api_resumen_organismos` (bodega → s3://pdc-api) y `pdc_api_resumen_organismos_ingest` (S3 → DocumentDB con renombre atómico); `sql/api/resumen_organismos.sql` con HHI y top 5 proveedores. Cargados julio, agosto y septiembre (1.149 organismos en septiembre).
- Emulador de Glue: soporte de `--additional-python-modules` y entrypoint `bash -c` explícito (la imagen ya usa bash como entrypoint).
- Lambda `pdc-api-compras` (arm64, pymongo empaquetado con `scripts/empaquetar_lambda.sh`) y API Gateway REST `v1` con dos endpoints, API key obligatoria y plan de uso. Probado: 200 con key, 403 sin key o con key falsa, 404 y 400.
- Limitaciones de floci resueltas: API key por CLI (`scripts/crear_api_key.sh`) porque el provider de Terraform falla al leerla; `ignore_changes` en `timeout_milliseconds`; se borraron 2 APIs y 2 keys huérfanas del apply abortado. ADR-012.
- DAG diario extendido con los jobs de la API; `scripts/publicar_dags.sh` porque floci no resincroniza DAGs desde S3.
- Ejecución manual del DAG con las 6 tareas: `glue_vw_ordenes_compra_items` falló (FAILED sin excepción en el log; posible falta de memoria con dos ejecuciones simultáneas, sin verificar). Se detuvieron todos los servicios para liberar recursos; pendiente en TODO.
- Nota `RETOMAR.md` con los pasos para levantar el entorno de nuevo.

## 2026-10-21

- Credenciales del DTPM recibidas, guardadas en `.env` (DTPM_USUARIO, DTPM_CLAVE) y probadas: posiciones (13.946 registros) y alertas (1.006) responden 200. Nota `fuentes/DTPM_Web_Services`; DUDAS 2 resuelta.
- Documentación oficial del DTPM agregada en `docs/` (PDFs de posicionamiento y alertas, archivo DECO de servicios). `DTPM_Web_Services` reescrita con los 12 campos oficiales por transmisión, tipos de alerta, códigos de error, perfil de la consulta del 2026-10-21 (6.128 buses activos en 5 min, 721 servicios, 1.006 alertas) e ideas para la fase 7. `Transporte_Tiempo_Real` pasa del simulador al feed real.
- README: sección "Proyectos relacionados" con enlace a `indice-salud-cl` (repo público aparte, dominio de salud).

## 2026-11-01

- Fase 6: esquema `monitoreo` (`plataforma/sql/monitoreo/01_ddl.sql`), Lambda `pdc-monitoreo` (`plataforma/lambdas/monitoreo`, pg8000 contra la bodega) y `plataforma/terraform/monitoreo.tf`. Chequeos: frescura del CSV en raw (máx. 36 h), caída de ítems mayor al 10% contra la medición anterior e ítems sin órdenes. Cada falla crea una alerta; si hay `OPENROUTER_API_KEY` pide una explicación al modelo `openrouter/free` (ADR-005).
- DAG `dag_compras_diario`: tarea final `monitoreo_calidad` que invoca la Lambda por mes.
- Probado: borrado del 20% de septiembre (71.110 ítems) hizo fallar `volumen_items` (355.585 a 284.475); tras restaurar volvió a `ok`. `frescura_raw` falla de verdad: el archivo de septiembre tiene más de 34 días. La explicación del modelo llegó en una de tres alertas (el modelo gratuito es intermitente).
- `empaquetar_lambda.sh`: no falla con Lambdas de `plataforma/lambdas/` y empaqueta sin `.pyc` (OneDrive daba timeouts al leerlos). `recrear_mwaa.sh` pasa `docdb_password` y la clave de OpenRouter.
- `scramp` fijado en 1.4.5 porque `pg8000` 1.31.2 falla con versiones nuevas.
- Grafana 11 en `docker-compose.yml` (puerto 3000, acceso anónimo solo local) con datasource `Bodega` (rol `pdc_lector`) y panel `Monitoreo` provisionados desde `plataforma/grafana/`. Primera captura en `docs/capturas/grafana_monitoreo.png` mostrando la carga rota de septiembre y su recuperación.
- `docs/DEMO.md`: guion de demo de punta a punta con las ventanas a abrir (Airflow, Grafana, consola de floci, logs de Glue), qué decir en cada capa, la prueba de la carga rota y preguntas probables.
- `pdc_dim_compras`: si el mes no tiene partición de ítems (CSV sin filas a inicio de mes), termina en éxito sin cargar en vez de fallar con `PATH_NOT_FOUND`. Probado con 2026-09, que no tiene partición en analytics. Causa de los fallos de las corridas programadas del 2026-11-01. Pendiente aparte: los `glue_vw_ordenes_compra_items` mueren por memoria (137) con Docker en 7,65 GB.
- Fase 7: `dw.dim_servicio` (429) y `dw.dim_recorrido` (776, con sentido I/R) cargadas desde el diccionario DECO con `dominios/transporte/scripts/cargar_deco.sh` (DDL en `dominios/transporte/sql/bodega/10_ddl_transporte.sql`). Idempotente: una segunda corrida deja los mismos conteos. Un servicio con varias rutas toma los datos de la primera por código de ruta. Falta el GTFS estático (trazados, paraderos, horarios): no existe en el repo ni en el vault.
- Fase 7, productor y consumidor: `terraform/transporte.tf` crea el stream Kinesis `pdc-posiciones`, la tabla DynamoDB `pdc-buses-actuales` (clave `patente`), el secreto `pdc/dtpm`, las Lambdas `pdc-productor-posiciones` y `pdc-consumidor-posiciones` (esta con mapeo desde Kinesis) y el schedule `pdc-productor-posiciones-minuto` (rate 1 minuto, **deshabilitado**: se activa a mano). El productor se queda con la última transmisión de los buses con GPS de menos de 5 min; el consumidor deja el último estado por patente en DynamoDB y el micro-lote en `s3://pdc-raw/transporte/posiciones/fecha=/hora=/`.
- Probado con una invocación: 13.980 buses en la respuesta, 3.467 activos, 0 fallidos en Kinesis, 3.467 patentes en DynamoDB y 3 micro-lotes en S3. `providers.tf` suma los endpoints de kinesis y dynamodb (sin ellos Terraform salía a AWS real). El DDL de transporte pasó a `10_ddl_transporte.sql` porque Terraform sube todos los `sql/` de `dominios/` al mismo prefijo y chocaba con el de compras.
- Fase 7, API: Lambda `pdc-api-transporte` y `GET /transporte/buses?servicio=T502&sentido=I&limite=N` en el mismo API Gateway (misma API key y plan de uso). Lee DynamoDB con scan filtrado (atajo anotado en el código). Probado: 403 sin clave; con clave devuelve los buses activos del servicio, y entre dos consultas la posición de un bus cambió.
- Productor: latitud, longitud y velocidad se guardan como número (salían como texto) y un bus con valores malformados se descarta en vez de romper la invocación. Prueba con casos sintéticos: filtra la transmisión de 2023 y el valor vacío.
- `docs/PUNTA_A_PUNTA.md`: guía de punta a punta con dos diagramas Mermaid (plataforma completa y secuencia del DAG), una sección por capa con su ADR y archivo, tabla emulado contra AWS real, limitaciones y diez preguntas de entrevista. Los diagramas se renderizaron sin errores de sintaxis.
- `dominios/transporte/scripts/mapa_buses.py` genera una página Leaflet con los buses activos de DynamoDB; primera captura en `docs/capturas/mapa_buses.png` (3.849 buses sobre Santiago). El HTML generado no se versiona.
