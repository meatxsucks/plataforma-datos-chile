# Llevar la plataforma a otro PC

Código y documentación viajan por git. Los **datos** (lago, bodega, DocumentDB) y los **secretos** no: pesan unos 3 GB y el `.env` nunca se sube.

## Qué se lleva y cómo

| Qué | Dónde vive | Cómo viaja |
|---|---|---|
| Código, DAGs, Terraform, docs, `spec/` | repo `meatxsucks/plataforma-datos-chile` | `git clone` |
| Notas | repo `meatxsucks/vault` | `git clone` |
| Lago S3, estado de floci (Lambdas, API, Airflow) | `~/.pdc/floci-data` (2,9 GB) | `floci-data.tar.gz` |
| Bodega Postgres (`dw`, `stage`, `monitoreo`) | volumen Docker de RDS | `bodega.dump` (pg_dump) |
| API Mongo | volumen Docker de DocumentDB | `docdb.archive.gz` (mongodump) |
| Estado de Terraform | `plataforma/terraform/terraform.tfstate` (gitignored) | archivo suelto |
| Secretos | `.env` (gitignored) | archivo `env`, solo por canal privado |

## En el PC de origen

```bash
# stack arriba (floci, rds y docdb corriendo)
plataforma/scripts/exportar_datos.sh ~/pdc-export
```

Copia `~/pdc-export` al otro PC con disco externo, `rsync` o `scp`. No lo subas a git ni a un drive compartido: incluye `env` con claves.

## En el PC de destino

Requisitos: Docker Desktop con al menos 10 GB de memoria, `terraform`, `git`, Python 3.12.

```bash
git clone https://github.com/meatxsucks/plataforma-datos-chile.git
cd plataforma-datos-chile
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
plataforma/scripts/importar_datos.sh /ruta/a/pdc-export
```

Verifica: Airflow en http://localhost:8080, Grafana en http://localhost:3000, y la API con la API key de `.env`.

## Si prefieres no mover 3 GB

El lago se reconstruye desde cero: `terraform apply`, extraer con la Lambda `pdc-extractor-oc-masiva` (necesita `MERCADOPUBLICO_TICKET`) y correr el DAG. Tarda horas y depende de que Mercado Público siga sirviendo esos meses, por eso la copia es más segura.

## Prompt para un agente

Pégalo tal cual en Claude Code en el PC nuevo, dentro de la carpeta donde quieras el proyecto.

```
Debes dejar funcionando en este PC la plataforma "plataforma-datos-chile", migrada desde otro equipo. Trabaja en español; los commits van en español, sin menciones a herramientas de asistencia ni coautores.

CONTEXTO
- Repo de código: https://github.com/meatxsucks/plataforma-datos-chile (rama main). Repo de notas: https://github.com/meatxsucks/vault (nota Notas/plataforma-datos-chile.md). Léelas primero, junto con docs/PUNTA_A_PUNTA.md, docs/MIGRAR_OTRO_PC.md y spec/CHANGELOG.md.
- Es una plataforma de datos de compras públicas de Chile sobre floci (AWS emulado en localhost:4566): lago S3 (pdc-raw, pdc-analytics, pdc-sensible, pdc-api), Glue (emulador glue-jobs, puerto 4567), Airflow/MWAA (UI 8080 por socat), bodega Postgres (RDS, proxy localhost:7001, base bodega), DocumentDB, API Gateway, Lambdas (incluye monitoreo y transporte en tiempo real) y Grafana (3000).
- Los datos NO están en git. El usuario traerá una carpeta "pdc-export" con: bodega.dump, docdb.archive.gz, floci-data.tar.gz, terraform.tfstate, env (secretos) y SHA256SUMS. Pídele la ruta.

REGLAS
1. No ejecutes nada destructivo (docker system prune, borrar volúmenes, rm -rf de ~/.pdc) sin pedir confirmación.
2. No subas nunca el archivo env/.env ni el contenido de pdc-export a git ni a ningún servicio.
3. Si algo falla, diagnostica con logs (docker logs, airflow tasks logs) antes de cambiar código. Informa qué falló y por qué, sin esconder errores.
4. Solo un stack a la vez: el floci de datos y el de finanzas comparten los puertos 4566 y 7001. Si hay otro floci corriendo, pregunta antes de detenerlo.

PASOS
1. Verifica requisitos: git, Docker Desktop con al menos 10 GB de memoria (en macOS: settings-store.json, clave MemoryMiB), terraform, Python 3.12. Instala lo que falte pidiendo permiso.
2. Clona ambos repos. En plataforma-datos-chile crea .venv e instala requirements-dev.txt.
3. Verifica la integridad: cd pdc-export && shasum -a 256 -c SHA256SUMS. Si falla un hash, detente y avisa.
4. Ejecuta plataforma/scripts/importar_datos.sh <ruta pdc-export>. Revisa cada etapa: restaura .env, tfstate y ~/.pdc/floci-data, levanta docker compose, inicia floci-rds y floci-docdb, restaura Postgres y Mongo, recrea Airflow y publica los DAGs.
5. Comprueba que los datos llegaron:
   - S3: con AWS_ACCESS_KEY_ID=test, AWS_SECRET_ACCESS_KEY=test, región us-east-1 y --endpoint-url http://localhost:4566, "aws s3 ls" debe listar pdc-raw, pdc-analytics, pdc-sensible, pdc-api y pdc-mwaa.
   - Postgres: psql -U pdc_admin -d bodega dentro del contenedor floci-rds (PGPASSWORD=$POSTGRES_PASSWORD); lista las tablas de dw y cuenta filas de la tabla de ítems. Referencia: Sept 2026 ≈ 355.585 ítems y Oct 2026 ≈ 465.899.
   - Mongo: base api_compras con colecciones y documentos.
   - Airflow: http://localhost:8080 muestra dag_compras_diario.
   - Grafana: http://localhost:3000 muestra el dashboard de monitoreo.
6. Ejecuta el DAG de punta a punta: airflow dags unpause y airflow dags trigger de dag_compras_diario dentro del contenedor de Airflow. Debe terminar en success (unos 3,5 min). Si Glue muere con código 137, es falta de memoria de Docker: sube MemoryMiB y reinicia Docker; no toques el código.
7. Prueba la API: obtén la URL con terraform -chdir=plataforma/terraform output url_api y llama a /transporte/buses?servicio=T502 y a los endpoints de compras con la cabecera x-api-key de API_KEY_DEMO.
8. Deja un resumen: qué se restauró, conteos verificados, qué quedó pendiente. Si cambias algo en el repo, haz commit en español y pregunta antes de hacer push.

NO HAGAS
- No habilites el scheduler pdc-productor-posiciones-minuto: está DISABLED a propósito (el servicio DTPM limita a 1 consulta por minuto y exige credenciales).
- No regeneres el lago desde cero a menos que la restauración falle y el usuario lo apruebe.

CRITERIO DE ÉXITO
Airflow, Grafana y la API responden; los conteos de la bodega coinciden con el origen; el DAG termina en success.
```
