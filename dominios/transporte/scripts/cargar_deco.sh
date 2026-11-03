#!/usr/bin/env bash
# Carga el diccionario DECO a la bodega: stage.deco -> dw.dim_servicio y dw.dim_recorrido.
# Uso: dominios/transporte/scripts/cargar_deco.sh [archivo.csv]
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../../.." && pwd)"
CSV="${1:-$(ls "$RAIZ"/dominios/transporte/docs/DECO_VIGENTES_*.csv | tail -1)}"
C=$(docker ps --format '{{.Names}}' | grep floci-rds | head -1)
PSQL=(docker exec -i "$C" psql -U pdc_admin -d bodega -v ON_ERROR_STOP=1 -q)

"${PSQL[@]}" < "$RAIZ/dominios/transporte/sql/bodega/10_ddl_transporte.sql"
"${PSQL[@]}" -c "TRUNCATE stage.deco"
"${PSQL[@]}" -c "\copy stage.deco FROM STDIN WITH (FORMAT csv, DELIMITER ';', HEADER)" < "$CSV"

# Un servicio puede traer varias rutas con datos distintos: se toma la primera por código de ruta
"${PSQL[@]}" <<'SQL'
INSERT INTO dw.dim_servicio (codigo_usuario, codigo_mtt, servicio_deco, tipo_servicio, unidad)
SELECT DISTINCT ON (codigo_usuario) codigo_usuario, codigo_mtt, servicio_deco, tipo_servicio, cli_dsc
FROM stage.deco ORDER BY codigo_usuario, codigo_ruta
ON CONFLICT (codigo_usuario) DO UPDATE SET
    codigo_mtt = EXCLUDED.codigo_mtt, servicio_deco = EXCLUDED.servicio_deco,
    tipo_servicio = EXCLUDED.tipo_servicio, unidad = EXCLUDED.unidad, actualizado_en = now();

INSERT INTO dw.dim_recorrido (codigo_ruta, codigo_usuario, sentido)
SELECT codigo_ruta, codigo_usuario, CASE WHEN right(codigo_ruta, 1) IN ('I', 'R') THEN right(codigo_ruta, 1) END
FROM stage.deco
ON CONFLICT (codigo_ruta) DO UPDATE SET
    codigo_usuario = EXCLUDED.codigo_usuario, sentido = EXCLUDED.sentido, actualizado_en = now();
SQL

"${PSQL[@]}" -tA -c "select 'servicios: '||count(*) from dw.dim_servicio union all select 'recorridos: '||count(*) from dw.dim_recorrido union all select 'sin sentido: '||count(*) from dw.dim_recorrido where sentido is null"
