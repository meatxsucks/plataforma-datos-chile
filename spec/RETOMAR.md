# Cómo retomar el proyecto

Estado al 2026-09-28: fases 1 a 5 construidas. La fase 5 (API) está probada con `curl`; falta confirmar la corrida completa del DAG (ver *Pendiente al pausar* en [[TODO]]).

## Levantar el entorno

Los contenedores de floci (Postgres, DocumentDB, Airflow y DuckDB) quedaron **detenidos, no borrados**: los datos de la bodega y de DocumentDB siguen ahí.

```bash
cd plataforma-datos-chile
docker compose up -d                                   # floci, glue-jobs, airflow-ui
docker ps -a --format '{{.Names}}' | grep -E '^floci-(rds|docdb|duck)' | xargs docker start
scripts/recrear_mwaa.sh                                # Airflow queda huérfano al reiniciar floci
scripts/publicar_dags.sh
```

Revisar después:

- `nc -z localhost 7001` responde (bodega).
- `curl -H "x-api-key: $API_KEY_DEMO" "$(terraform -chdir=infra/terraform output -raw url_api)/compras/alertas/concentracion"` responde 200.
- La interfaz de Airflow en `http://localhost:8080` (usuario `admin`; la clave se obtiene con `docker exec <contenedor airflow> printenv _AIRFLOW_WWW_USER_PASSWORD`).

## Siguiente paso

1. Resolver el fallo del DAG (ver [[TODO]]).
2. Fase 6: monitoreo (tablas de monitoreo, chequeos de frescura y volumen, alertas a Telegram con explicación vía OpenRouter).
