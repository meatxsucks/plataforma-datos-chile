# Plataforma de Datos Chile

Plataforma de datos de punta a punta sobre datos públicos chilenos, construida con servicios de AWS
emulados localmente con [floci](https://github.com/floci-io/floci): ingesta batch y en tiempo real,
lago en capas, jobs de Glue, bodega dimensional, APIs de datos, orquestación, monitoreo y gobernanza.

![Arquitectura](docs/diagramas/arquitectura_general.png)

## Dominios

| Dominio | Pregunta |
|---|---|
| Compras públicas (batch) | ¿Qué organismos concentran compras en pocos proveedores o en trato directo? |
| Transporte Santiago (tiempo real) | ¿Cuánto se desvía el servicio de buses del programado? |
| Economía regional (analítica) | ¿Cómo se mueven empleo y precios por región frente al país? |

## Requisitos

Docker, Terraform, Python 3.11, AWS CLI, Graphviz y `uv`.

## Levantar el entorno

```bash
cp .env.example .env                       # completar ticket de Mercado Público y clave de seudonimización
docker compose up -d                       # floci en localhost:4566
python3.11 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cd infra/terraform && terraform init && terraform apply && cd -
```

## Primer pipeline

```bash
.venv/bin/python scripts/extraer_ordenes_dia.py --fecha 2026-09-26 --limite 60
scripts/glue_local.sh pdc_vw_ordenes_compra --fechaParticion 2026-09-26 \
  --bucketOrigen pdc-raw --bucketDestino pdc-analytics --bucketSensible pdc-sensible \
  --baseDatos pdc --claveSeudonimo "$CLAVE_SEUDONIMO"
```

## Estructura

```
docs/diagramas/     diagramas como código (mingrammer/diagrams)
glue/jobs/          un script por job de Glue
infra/terraform/    infraestructura contra floci
lambdas/            código de las Lambdas
scripts/            utilitarios locales (extracción, Glue local, prueba de MCP)
spec/               documentación del proyecto (vault de Obsidian)
utils/              código compartido por jobs, Lambdas y DAGs
```

## Documentación

Arquitectura, decisiones (ADRs), dominios y fuentes en [`spec/`](spec/README.md).
