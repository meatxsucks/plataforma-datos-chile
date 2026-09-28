# ADR-007 — Diagramas de arquitectura como código

**Estado:** aceptada · **Fecha:** 2026-09-28

## Decisión

- **Principal:** `mingrammer/diagrams` (Python, MIT, íconos oficiales de AWS). El diagrama es un script versionado en `docs/diagramas/` que genera PNG y SVG para el README.
- **Alternativa editable:** draw.io con su librería AWS y `jgraph/drawio-mcp` o `aws-samples/sample-drawio-mcp`, cuando haga falta retocar a mano.

## Alternativas descartadas

| Opción | Motivo |
|---|---|
| `aws-diagram-mcp-server` (awslabs) | Deprecado |
| Terravision (desde Terraform, con MCP) | Interesante para generar desde la IaC; licencia no confirmada. Revisar en fase 9 |
| Excalidraw | Estética de boceto, sin íconos oficiales |
| Cloudcraft, Pluralith | De pago o cerrados |
| Inframap | Sin íconos AWS |

## Consecuencias

- Requiere Graphviz instalado (`brew install graphviz`).
- Un diagrama por vista: general, batch de compras, tiempo real y gobernanza.
