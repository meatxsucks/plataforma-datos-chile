# Dudas abiertas

| # | Duda | Opciones | Recomendación | Bloquea |
|---|---|---|---|---|
| 1 | El repo está dentro de OneDrive: sincronizar `.git`, volúmenes de Docker y datos locales puede corromper o saturar la sincronización | a) mover el repo fuera de OneDrive · b) dejarlo y excluir `data/` y `.venv` | **Resuelta 2026-09-28:** el repo se queda en OneDrive, riesgo asumido | — |
| 2 | Posiciones GPS de buses no son públicas | a) simulador desde GTFS · b) solicitar acceso al DTPM · c) ambas | c): partir con simulador y cambiar el productor si llega el acceso | Fase 7 |
| 3 | Herramienta de visualización | Superset · Metabase · Streamlit · Evidence | **Resuelta 2026-09-28:** Streamlit (Apache 2.0, gratis) | — |
| 4 | Docker: el cliente está instalado pero el daemon no corría el 2026-09-28 (Mac arm64). Hace falta memoria para floci + Airflow + Glue + Postgres + Mongo | — | **Resuelta 2026-09-28:** Docker 29.0.1 corriendo, 10 CPU y ~7,6 GB; Graphviz 15.1 instalado | — |
| 5 | Nombre del repo en GitHub | `plataforma-datos-chile` u otro | — | Fase 9 |
| 6 | Catálogo, metadata y linaje para gobernanza | OpenMetadata · DataHub · Marquez/OpenLineage | **Resuelta 2026-09-28:** OpenMetadata. Pendiente medir su consumo de RAM junto al resto del stack (16 GB) | Fase de gobernanza |
