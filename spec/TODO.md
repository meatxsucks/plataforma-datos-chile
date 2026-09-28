# TODO

Cada fase termina con algo que se puede demostrar. No se pasa de fase sin cumplir el criterio.

## Fase 0 — Documentación y decisiones
- [x] Vault con arquitectura, dominios, fuentes y ADRs iniciales
- [ ] Resolver [[DUDAS]] que bloquean la fase 1

## Fase 1 — Base local
- [x] `docker-compose.yml` con floci, persistencia configurada (floci 2.1.0, modo hybrid; sobrevive a reinicio)
- [x] Terraform con provider apuntando a floci: bucket de prueba y Lambda "hola"
- [x] Probar la imagen `aws-glue-libs` en arm64 leyendo y escribiendo en el S3 de floci (Glue 5, nativa arm64)
- [x] Esqueleto del repo: README raíz, estructura de carpetas y `utils/glue_utils.py` (se empaqueta cuando lo usen Lambdas y DAGs)
- [x] Probar `aws-api-mcp-server` contra floci: respeta `AWS_ENDPOINT_URL`, lee S3 y el catálogo de Glue; configurado en `.mcp.json` en modo solo lectura
- [x] MCP de Postgres (fase 3)
- [ ] MCP de MongoDB (fase 5)
- [x] Primer diagrama con `mingrammer/diagrams`: `docs/diagramas/arquitectura_general.py` → PNG y SVG
- [x] Diagrama rehecho con líneas ortogonales y fronteras AWS Cloud → Cuenta → Región
- [ ] Diagrama: íconos propios de Streamlit y OpenMetadata
- **Término:** `terraform apply` crea bucket y Lambda; un job de Glue local escribe Parquet en floci.

## Fase 2 — Compras: extracción y capas
- [x] Pedir el ticket de Mercado Público (probado 2026-09-28: 1.316 órdenes el 26-09-2026)
- [x] Lambda `pdc-extractor-oc-masiva` + EventBridge Scheduler diario 09:00 Chile (ver [[ADR-009_Extraccion_Archivo_Masivo]]); probada manual, idempotente y disparada por el programador
- [x] Backfill julio y agosto 2026 desde las descargas masivas de ChileCompra (`vw_ordenes_compra_items`, grano ítem)
- [x] Primer job `pdc_vw_ordenes_compra` con seudonimización (60 órdenes de muestra)
- [x] Verificar la tabla con Athena de floci: 60 filas, 60 códigos únicos, 3 personas naturales seudonimizadas; reejecución sin duplicar y 1 solo archivo
- [x] Job de ítems `pdc_vw_ordenes_compra_items`: 427.834 ítems en julio y 433.800 en agosto
- **Término:** una semana de órdenes consultable en Athena. **Cumplido 2026-09-28:** julio, agosto y septiembre (1.217.219 ítems) consultables en Athena.
- [ ] Licitaciones (archivo masivo `lic-da`) e InfoLobby

## Fase 3 — Bodega dimensional
- [x] Modelo en Postgres (dimensiones y hechos de [[Compras_Publicas]]): ver [[ADR-010_Modelo_Dimensional_Compras]]
- [x] Carga stage + DELETE/INSERT con job `pdc_dim_compras` y `sql/bodega/02_cargar_compras.sql`
- [x] MCP de Postgres con rol `pdc_lector` de solo lectura
- **Término:** conteos y claves únicas cuadran entre stg y la bodega. **Cumplido 2026-09-28** para julio, agosto y septiembre.
- [ ] Dimensión de producto (rubros ONU) si el análisis la necesita

## Fase 4 — Orquestación
- [x] Emulador de `StartJobRun`/`GetJobRun` ([[ADR-011_Emulador_Glue_Jobs]]) y jobs de Glue definidos en Terraform
- [x] MWAA `pdc-airflow` (Airflow 2.10.5) en VPC con subredes privadas, conexiones desde Secrets Manager
- [x] `dag_compras_diario`: meses a procesar → sensor de raw actualizado → Glue ítems → Glue bodega (tareas dinámicas por mes)
- **Término:** corrida completa disparada desde Airflow. **Cumplido 2026-09-28:** corrida manual y programada en `success`, bodega sin cambios de conteo (idempotente).
- [ ] Backfill con parámetros desde la interfaz de Airflow
- [ ] floci no expone un puerto estable para la web de MWAA: se usa `airflow-ui` (socat) en `localhost:8080`

## Fase 5 — API
- [x] DocumentDB `pdc-docdb` y jobs `pdc_api_resumen_organismos` + `_ingest` (julio a septiembre)
- [x] Lambda `pdc-api-compras` + API Gateway `v1` con API key y plan de uso ([[ADR-012_API_Datos_Compras]])
- [x] DAG diario extendido: bodega → API → ingesta
- **Término:** `curl` con API key responde con datos; sin key responde 403. **Cumplido 2026-09-28.**
- [ ] Endpoint de proveedores (`/compras/proveedores/{codigo}/ordenes`)

## Pendiente al pausar (2026-09-28)
- [ ] **Fallo en `dag_compras_diario` (manual__2026-09-28T18:20:06):** `glue_vw_ordenes_compra_items` terminó en FAILED dos veces sin excepción en el log de Spark; el log se corta mientras cachea bloques. Hipótesis no verificada: el contenedor se quedó sin memoria (código 137) porque corrían dos ejecuciones del DAG a la vez, cada una con 4 GB de driver, junto a Airflow (~1,8 GB) y floci (~1,8 GB) en 7,6 GB de Docker. La otra ejecución (manual__2026-09-28T18:22:05) se marcó a mano como success desde la interfaz y **no procesó datos**.
- [ ] Propuesta para el emulador (no aplicada): driver de 3 GB, `spark.sql.shuffle.partitions=16` y un `ErrorMessage` que informe el código de salida (137 = sin memoria). Confirmar la causa revisando el código de salida antes de cambiar nada.
- [ ] Reintentar la ejecución fallida desde la interfaz (Clear sobre las tareas de Glue) y confirmar que llega hasta la ingesta de la API.

## Fase 6 — Monitoreo
- [ ] Tablas de monitoreo, chequeos de frescura y volumen, alertas
- **Término:** una carga rota a propósito genera alerta.

## Fase 6b — Gobernanza
- [ ] OpenMetadata en Docker (por turnos), ingesta de metadata de Postgres y Airflow, glosario y dueños
- [ ] Great Expectations en jobs y DAGs, resultados publicados en OpenMetadata
- [ ] Explicación de alertas con OpenRouter
- **Término:** linaje de punta a punta de una tabla de compras visible en OpenMetadata, y una validación fallida que aparece en el catálogo y genera alerta explicada.

## Fase 7 — Transporte en tiempo real
- [x] Solicitud al DTPM enviada el 2026-09-28 (respuesta esperada en 10 días hábiles)
- [ ] GTFS estático a la bodega
- [ ] Productor simulado → Kinesis → Lambda → DynamoDB + S3
- [ ] Glue horario de puntualidad
- **Término:** API devuelve buses activos de un recorrido y su puntualidad de la última hora.

## Fase 8 — Economía regional y visualización
- [ ] Extracción BDE, CMF e INE
- [ ] Transformaciones: homologación, deflactación, STL, rezagos
- [ ] Tablero
- **Término:** tablero con mapa regional y cruce con compras deflactadas.

## Fase 9 — Portafolio
- [ ] README con diagrama, cómo levantarlo y decisiones
- [ ] Publicar en GitHub (meatxsucks)
