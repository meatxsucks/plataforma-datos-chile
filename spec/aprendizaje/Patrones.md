# Patrones que el proyecto practica

Patrones genéricos de plataformas de datos en AWS. Aquí se describen en abstracto; la implementación
del proyecto se escribe desde cero.

| Patrón | Qué resuelve | Dónde se practica |
|---|---|---|
| Capas raw → stg → analytics | Separar el dato tal como llegó del dato limpio y del modelado; reprocesar sin volver a extraer | Todos los dominios |
| Stage + DELETE/INSERT | Cargas idempotentes por rango en la bodega | Carga a Postgres |
| Silver en S3 → gold en documento | Servir APIs con baja latencia sin consultar la bodega | INGEST a DocumentDB |
| Colección por fecha de corte | Publicar un corte nuevo sin romper a quien lee el anterior | DocumentDB |
| API Gateway + API keys + usage plans | Identificar consumidores y limitar su uso | APIs de lectura |
| Sensor de datos disponibles | Encadenar procesos por disponibilidad del dato y no por hora fija | DAGs de Airflow |
| Tablas de monitoreo + alertas | Saber qué corrió, cuánto cargó y si llegó a tiempo | Monitoreo |
| Librería compartida | Un solo lugar para conexiones, logging y utilidades comunes a Lambdas, Glue y DAGs | Paquete `utils` |
| Infra como código | Reconstruir el entorno completo desde cero | Terraform contra floci |
| Estado actual e historia por separado | Consultar lo último rápido sin perder el histórico | Transporte: DynamoDB y S3 |
