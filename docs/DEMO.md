# Demo guiada, de punta a punta

Guion para ejecutar el pipeline de compras mirándolo en vivo y poder explicar cada capa. Dura ~15 minutos
con los datos ya cargados.

## Antes de empezar

```bash
docker compose up -d                                   # floci, glue-jobs, airflow-ui, grafana
docker ps -a --format '{{.Names}}' | grep -E '^floci-(rds|docdb)' | xargs docker start
plataforma/scripts/recrear_mwaa.sh                     # Airflow queda huérfano al reiniciar floci
plataforma/scripts/publicar_dags.sh
```

Si Docker acaba de arrancar, espera a que `floci` aparezca como `healthy` en `docker ps`.

## Ventanas

| Ventana | Dirección | Qué se ve |
|---|---|---|
| Airflow | <http://localhost:8080> (usuario `admin`) | El DAG, cada tarea y sus logs |
| Grafana | <http://localhost:3000> | Chequeos, alertas y volumen |
| floci | <http://localhost:4566/_floci/ui> | Los servicios de AWS emulados |
| Terminal | `docker logs -f glue-jobs` | El Glue ejecutándose por dentro |

La clave de `admin` de Airflow:

```bash
docker exec $(docker ps --format '{{.Names}}' | grep pdc-airflow-airflow) printenv _AIRFLOW_WWW_USER_PASSWORD
```

## Recorrido

### 1. Las fuentes (ingesta batch)
- **Mostrar:** `s3://pdc-raw/compras/ordenes_compra_masiva/` en la consola de floci.
- **Decir:** una Lambda programada con EventBridge Scheduler baja cada día el zip mensual de ChileCompra y lo
  descomprime en streaming a raw. Es idempotente por ETag: si el archivo no cambió, devuelve `sin_cambios`.

### 2. Disparar el DAG
- **Hacer:** en Airflow, `dag_compras_diario`, botón de play (Trigger DAG).
- **Mostrar:** vista *Graph*. Las tareas se encienden en orden:
  `esperar_raw_actualizado` → `glue_vw_ordenes_compra_items` → `glue_dim_compras` →
  `glue_api_resumen_organismos` → `glue_api_resumen_organismos_ingest` → `monitoreo_calidad`.
- **Decir:** el sensor espera a que raw tenga el archivo del día; así el DAG no procesa datos viejos.
- **Cuidado:** la última corrida registrada falló por memoria en una tarea de Glue (ver `spec/TODO.md`).
  Si pasa, se reintenta con *Clear* sobre la tarea; no cambia lo que se explica.

### 3. Los jobs de Glue (lago en capas)
- **Mostrar:** `docker logs -f glue-jobs` mientras corre cada tarea.
- **Decir:** raw (CSV) pasa a analytics (Parquet particionado) con Spark. En el camino se **seudonimizan** los
  proveedores persona natural: el token queda en analytics y el diccionario que lo revierte, aparte, en
  `pdc-sensible` (ADR-008).

### 4. La bodega dimensional
- **Mostrar:** en una terminal,
  ```bash
  docker exec -it $(docker ps --format '{{.Names}}' | grep floci-rds | head -1) psql -U pdc_admin -d bodega
  ```
  y `select mes, count(*) from dw.fact_orden_compra_item group by 1 order by 1;`
- **Decir:** modelo dimensional con hechos de orden e ítem, carga con `MERGE`, y SCD 2 solo en el nombre del
  proveedor (ADR-010). Julio a septiembre cuadran contra Athena (octubre está cargado pero aún sin cuadrar).

### 5. La API de datos
- **Mostrar:**
  ```bash
  set -a; source .env; set +a
  URL=$(terraform -chdir=plataforma/terraform output -raw url_api)
  curl -H "x-api-key: $API_KEY_DEMO" "$URL/compras/alertas/concentracion?hhi_min=5000&limite=10"
  curl "$URL/compras/alertas/concentracion"      # sin clave: 403
  ```
- **Decir:** API Gateway con API key, Lambda y DocumentDB como almacén de lectura. El resumen se calcula en
  Glue y se ingesta aparte, así la API responde sin tocar la bodega (ADR-012).

### 6. Monitoreo (fase 6)
- **Mostrar:** Grafana, panel *Monitoreo*; la tarea `monitoreo_calidad` en Airflow.
- **Prueba de la carga rota:** respaldar y borrar el 20% de un mes, correr la Lambda, restaurar.
  ```bash
  C=$(docker ps --format '{{.Names}}' | grep floci-rds | head -1)
  docker exec $C psql -U pdc_admin -d bodega -c "create table public.respaldo_demo as select * from dw.fact_orden_compra_item where mes='2026-09' and id_item % 5 = 0"
  docker exec $C psql -U pdc_admin -d bodega -c "delete from dw.fact_orden_compra_item f using public.respaldo_demo r where f.id_item=r.id_item"
  aws --endpoint-url http://localhost:4566 lambda invoke --function-name pdc-monitoreo --cli-binary-format raw-in-base64-out --payload '{"mes":"2026-09"}' /dev/stdout
  # restaurar siempre:
  docker exec $C psql -U pdc_admin -d bodega -c "insert into dw.fact_orden_compra_item select * from public.respaldo_demo; drop table public.respaldo_demo"
  ```
- **Decir:** tres chequeos (frescura de raw, caída de volumen mayor al 10%, ítems sin órdenes). Cada falla crea
  una alerta y, si hay clave, un modelo de OpenRouter propone la causa. La alerta nunca depende del modelo
  (ADR-005).

## Preguntas que conviene tener listas

- **¿Por qué floci y no AWS real?** Costo cero y todo reproducible en local; el código y Terraform son los de
  AWS, solo cambia el endpoint (ADR-001).
- **¿Qué cambiaría en producción?** Redshift o Athena en vez de Postgres como bodega, MWAA real, secretos con
  rotación, y los DAGs desplegados desde CI en vez de copiados al contenedor.
- **¿Cómo se protegen los datos personales?** Seudonimización en el job y diccionario en un bucket aparte con
  acceso restringido (ADR-008).
- **¿Cómo sabes que los números están bien?** Cuadre de ítems, órdenes y monto contra Athena en cada mes, sin
  duplicados ni huérfanos (CHANGELOG, fase 3).
- **¿Qué falla hoy?** `frescura_raw` alerta porque el archivo de septiembre tiene más de un mes; el modelo
  gratuito de OpenRouter es intermitente y a veces la alerta sale sin explicación.
