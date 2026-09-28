# ADR-008 — Protección de datos personales en compras públicas

**Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

El detalle de las órdenes de compra trae datos de personas naturales: contactos del comprador y del proveedor (nombre, teléfono, correo) y, cuando el proveedor es persona natural, su nombre y RUT. Aunque la fuente es pública, el proyecto aplica los principios de la ley de protección de datos personales (Ley 19.628 y su reforma, Ley 21.719): finalidad, minimización y seguridad.

## Decisión

| Principio | Aplicación |
|---|---|
| Minimización | Los datos de contacto no pasan de raw; el job de analytics no los selecciona |
| Seudonimización | Si el proveedor es persona natural, su RUT se reemplaza por `sha2(clave_secreta ‖ rut_normalizado, 256)` y su nombre por `PERSONA NATURAL` |
| Separación | El diccionario token → RUT y nombre se escribe en el bucket `pdc-sensible`, fuera del catálogo analítico |
| Marca explícita | Columna `es_persona_natural` para filtrar y auditar |
| Secreto | La clave vive en Secrets Manager (`pdc/seudonimo`), cargada por Terraform desde `.env`; el job la lee con `obtener_secreto` |

Regla de persona natural: RUT menor a 50.000.000. Es una aproximación conocida (las personas jurídicas suelen tener RUT sobre ese número); se documenta como heurística.

## Consecuencias

- Los análisis de concentración siguen funcionando: el token es estable, así que el mismo proveedor suma bajo el mismo token entre días.
- Re-identificar exige acceso a `pdc-sensible` y a la clave.
- raw conserva los datos originales: su acceso debe restringirse (política IAM en fase de gobernanza).
- Resuelto 2026-09-28: la clave ya no viaja como argumento del job.
- Mejora pendiente: HMAC-SHA256 en lugar de hash con clave concatenada.
- En OpenMetadata, las columnas se etiquetarán como `PII.Sensitive` o `PII.NonSensitive`.
