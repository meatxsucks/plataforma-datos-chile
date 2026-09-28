# ADR-001 — floci como emulador de AWS

**Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

El proyecto busca practicar servicios de AWS (Lambda, API Gateway, MWAA, Glue, Kinesis, DocumentDB) sin
costo y sin cuenta en la nube.

## Decisión

Usar floci (MIT) como emulador local en `http://localhost:4566`, levantado con Docker Compose.

## Alternativas

- LocalStack: la versión gratuita no incluye varios de los servicios que se necesitan (MWAA, DocumentDB, Glue).
- Cuenta real de AWS con capa gratuita: tiene costo potencial y no permite romper cosas sin cuidado.

## Consecuencias

- Glue y Redshift no ejecutan cargas en floci: ver [[ADR-002_Glue_Local]] y [[ADR-003_Postgres_Como_Bodega]].
- El estado es en memoria por defecto: hay que configurar persistencia o reconstruir con Terraform.
- Todo el código usa el endpoint configurable, así que podría correr contra AWS real cambiando variables.
