# ADR-011 — Emulador de ejecuciones de Glue para orquestar desde MWAA

**Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

floci guarda la definición de los jobs de Glue (`CreateJob`, `GetJob`) pero responde `Action StartJobRun is not supported`. Sin eso, un DAG con `GlueJobOperator` no puede ejecutar nada.

## Decisión

Servicio `glue-jobs` en docker-compose (`emuladores/glue_jobs/app.py`, ~150 líneas):

- Atiende la API JSON 1.1 de Glue en `http://glue-jobs:4567`.
- `StartJobRun`: lee el job desde floci (`GetJob`), baja el script y `--extra-py-files` desde S3 a un volumen compartido y lanza el contenedor oficial `aws-glue-libs:5` con los argumentos por defecto más los de la ejecución.
- `GetJobRun` / `GetJobRuns`: estado en memoria (`STARTING`, `RUNNING`, `SUCCEEDED`, `FAILED`), tiempo de ejecución y mensaje de error.
- Cualquier otra operación se reenvía tal cual a floci.

En Airflow, la conexión `aws_default` vive en Secrets Manager (`airflow/connections/aws_default`, backend `SecretsManagerBackend`, igual que en MWAA real) y redirige solo Glue con `service_config.glue.endpoint_url`. El resto de los servicios usa floci.

## Alternativas

| Opción | Motivo del descarte |
|---|---|
| Operador propio que llame a un lanzador | El DAG deja de ser el que correría en AWS |
| Orquestar solo Lambdas | La orquestación queda incompleta |

## Consecuencias

- Los DAGs usan `GlueJobOperator` sin cambios; en AWS real basta quitar `service_config` del secreto.
- Los jobs se definen en Terraform (`aws_glue_job`) con script, utilidades y SQL en `s3://pdc-glue-assets`.
- El estado de las ejecuciones se pierde si se reinicia el emulador; los logs quedan en el volumen `pdc-glue-trabajo`.
- Varios jobs a la vez compiten por la memoria de Docker: los DAGs limitan a una ejecución por tarea.
