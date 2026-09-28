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
- [ ] MCP de Postgres y MongoDB cuando existan esas bases (fases 3 y 5)
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
- [ ] Modelo en Postgres (dimensiones y hechos de [[Compras_Publicas]])
- [ ] Carga stage + DELETE/INSERT
- **Término:** conteos y claves únicas cuadran entre stg y la bodega.

## Fase 4 — Orquestación
- [ ] DAG de compras con sensores y backfill
- **Término:** corrida completa disparada desde Airflow.

## Fase 5 — API
- [ ] INGEST a DocumentDB
- [ ] Lambda de lectura + API Gateway + API keys
- **Término:** `curl` con API key responde con datos; sin key responde 403.

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
