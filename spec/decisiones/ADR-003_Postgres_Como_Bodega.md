# ADR-003 — Postgres como bodega en lugar de Redshift

**Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

floci emula el control plane de Redshift, pero no ejecuta SQL.

## Decisión

Usar Postgres (RDS de floci) como bodega dimensional. Se mantiene el patrón de carga de Redshift:
escribir a una `stage_table`, y en una transacción hacer DELETE del rango y INSERT desde stage.

## Alternativas

- DuckDB como bodega: muy rápido, pero sin concurrencia de escritura ni el patrón cliente-servidor.
- Athena sobre S3 como única capa de consulta: no practica modelado ni cargas transaccionales.

## Consecuencias

- El SQL se escribe evitando extensiones exclusivas de Postgres cuando haya equivalente en Redshift,
  para que la migración conceptual sea directa.
- Particularidades de Redshift (distkey, sortkey, COPY desde S3) quedan documentadas como diferencia, no se practican.
