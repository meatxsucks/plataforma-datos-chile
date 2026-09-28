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
