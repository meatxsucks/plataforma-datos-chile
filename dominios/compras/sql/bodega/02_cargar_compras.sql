MERGE INTO dw.dim_organismo d
USING (
    SELECT codigo_organismo, max(nombre_organismo) AS nombre_organismo, max(sector) AS sector
    FROM stage.oc_items
    WHERE codigo_organismo IS NOT NULL
    GROUP BY codigo_organismo
) s ON d.codigo_organismo = s.codigo_organismo
WHEN MATCHED AND (d.nombre_organismo IS DISTINCT FROM s.nombre_organismo OR d.sector IS DISTINCT FROM s.sector) THEN
    UPDATE SET nombre_organismo = s.nombre_organismo, sector = s.sector, actualizado_en = now()
WHEN NOT MATCHED THEN
    INSERT (codigo_organismo, nombre_organismo, sector) VALUES (s.codigo_organismo, s.nombre_organismo, s.sector);

MERGE INTO dw.dim_unidad_compra d
USING (
    SELECT codigo_unidad, max(nombre_unidad) AS nombre_unidad, max(rut_unidad) AS rut_unidad,
           max(region_unidad) AS region_unidad, max(codigo_organismo) AS codigo_organismo
    FROM stage.oc_items
    WHERE codigo_unidad IS NOT NULL
    GROUP BY codigo_unidad
) s ON d.codigo_unidad = s.codigo_unidad
WHEN MATCHED AND (d.nombre_unidad IS DISTINCT FROM s.nombre_unidad OR d.region_unidad IS DISTINCT FROM s.region_unidad) THEN
    UPDATE SET nombre_unidad = s.nombre_unidad, rut_unidad = s.rut_unidad, region_unidad = s.region_unidad,
               codigo_organismo = s.codigo_organismo, actualizado_en = now()
WHEN NOT MATCHED THEN
    INSERT (codigo_unidad, nombre_unidad, rut_unidad, region_unidad, codigo_organismo)
    VALUES (s.codigo_unidad, s.nombre_unidad, s.rut_unidad, s.region_unidad, s.codigo_organismo);

CREATE TEMP TABLE proveedor_origen AS
SELECT codigo_proveedor, max(rut_proveedor) AS rut_proveedor, max(nombre_proveedor) AS nombre_proveedor,
       max(actividad_proveedor) AS actividad_proveedor, max(region_proveedor) AS region_proveedor,
       bool_or(es_persona_natural) AS es_persona_natural
FROM stage.oc_items
WHERE codigo_proveedor IS NOT NULL
GROUP BY codigo_proveedor;

UPDATE dw.dim_proveedor d
SET rut_proveedor = s.rut_proveedor, actividad_proveedor = s.actividad_proveedor,
    region_proveedor = s.region_proveedor, es_persona_natural = s.es_persona_natural
FROM proveedor_origen s
WHERE d.codigo_proveedor = s.codigo_proveedor
  AND d.es_vigente
  AND (d.actividad_proveedor IS DISTINCT FROM s.actividad_proveedor
       OR d.region_proveedor IS DISTINCT FROM s.region_proveedor
       OR d.rut_proveedor IS DISTINCT FROM s.rut_proveedor);

UPDATE dw.dim_proveedor d
SET nombre_proveedor = s.nombre_proveedor
FROM proveedor_origen s
WHERE d.codigo_proveedor = s.codigo_proveedor
  AND d.es_vigente
  AND d.vigente_desde >= CAST('{fecha_efectiva}' AS DATE)
  AND d.nombre_proveedor IS DISTINCT FROM s.nombre_proveedor;

UPDATE dw.dim_proveedor d
SET vigente_hasta = CAST('{fecha_efectiva}' AS DATE) - 1, es_vigente = FALSE
FROM proveedor_origen s
WHERE d.codigo_proveedor = s.codigo_proveedor
  AND d.es_vigente
  AND d.vigente_desde < CAST('{fecha_efectiva}' AS DATE)
  AND d.nombre_proveedor IS DISTINCT FROM s.nombre_proveedor;

INSERT INTO dw.dim_proveedor (codigo_proveedor, rut_proveedor, nombre_proveedor, actividad_proveedor,
                              region_proveedor, es_persona_natural, vigente_desde)
SELECT s.codigo_proveedor, s.rut_proveedor, s.nombre_proveedor, s.actividad_proveedor,
       s.region_proveedor, s.es_persona_natural, CAST('{fecha_efectiva}' AS DATE)
FROM proveedor_origen s
WHERE NOT EXISTS (
    SELECT 1 FROM dw.dim_proveedor d WHERE d.codigo_proveedor = s.codigo_proveedor AND d.es_vigente
);

DROP TABLE proveedor_origen;

DELETE FROM dw.fact_orden_compra_item WHERE mes = '{mes}';

INSERT INTO dw.fact_orden_compra_item
SELECT i.id_item, i.codigo, i.mes, o.sk_organismo, p.sk_proveedor,
       CAST(to_char(i.fecha_envio, 'YYYYMMDD') AS INTEGER),
       i.codigo_producto_onu, i.producto_generico, i.rubro_n1, i.rubro_n2, i.rubro_n3,
       i.cantidad, i.unidad_medida, i.moneda_item, i.precio_neto, i.total_linea_neto
FROM stage.oc_items i
LEFT JOIN dw.dim_organismo o ON o.codigo_organismo = i.codigo_organismo
LEFT JOIN dw.dim_proveedor p ON p.codigo_proveedor = i.codigo_proveedor AND p.es_vigente;

DELETE FROM dw.fact_orden_compra WHERE mes = '{mes}';

INSERT INTO dw.fact_orden_compra
SELECT i.codigo, max(i.mes), max(o.sk_organismo), max(u.sk_unidad), max(p.sk_proveedor),
       max(CAST(to_char(i.fecha_creacion, 'YYYYMMDD') AS INTEGER)),
       max(CAST(to_char(i.fecha_envio, 'YYYYMMDD') AS INTEGER)),
       max(i.tipo), bool_or(i.es_trato_directo), bool_or(i.es_compra_agil), max(i.codigo_estado),
       max(i.codigo_licitacion), max(i.moneda_oc), max(i.monto_total_oc), max(i.monto_total_oc_clp),
       max(i.total_neto_oc), count(*)
FROM stage.oc_items i
LEFT JOIN dw.dim_organismo o ON o.codigo_organismo = i.codigo_organismo
LEFT JOIN dw.dim_unidad_compra u ON u.codigo_unidad = i.codigo_unidad
LEFT JOIN dw.dim_proveedor p ON p.codigo_proveedor = i.codigo_proveedor AND p.es_vigente
GROUP BY i.codigo;
