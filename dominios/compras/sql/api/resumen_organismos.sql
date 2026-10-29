WITH oc AS (
    SELECT o.codigo_organismo, o.nombre_organismo, o.sector,
           p.codigo_proveedor, p.nombre_proveedor, p.rut_proveedor,
           f.monto_total_oc_clp, f.es_trato_directo, f.es_compra_agil
    FROM dw.fact_orden_compra f
    JOIN dw.dim_organismo o ON o.sk_organismo = f.sk_organismo
    JOIN dw.dim_proveedor p ON p.sk_proveedor = f.sk_proveedor
    WHERE f.mes = '{mes}' AND f.monto_total_oc_clp > 0
),
por_proveedor AS (
    SELECT codigo_organismo, codigo_proveedor,
           max(nombre_proveedor) AS nombre_proveedor, max(rut_proveedor) AS rut_proveedor,
           sum(monto_total_oc_clp) AS monto_clp, count(*) AS ordenes
    FROM oc
    GROUP BY codigo_organismo, codigo_proveedor
),
totales AS (
    SELECT codigo_organismo, max(nombre_organismo) AS nombre_organismo, max(sector) AS sector,
           sum(monto_total_oc_clp) AS monto_clp, count(*) AS ordenes,
           count(DISTINCT codigo_proveedor) AS proveedores,
           sum(CASE WHEN es_trato_directo THEN monto_total_oc_clp ELSE 0 END) AS monto_trato_directo_clp,
           sum(CASE WHEN es_compra_agil THEN monto_total_oc_clp ELSE 0 END) AS monto_compra_agil_clp
    FROM oc
    GROUP BY codigo_organismo
),
ranking AS (
    SELECT p.*, t.monto_clp AS monto_organismo,
           ROW_NUMBER() OVER (PARTITION BY p.codigo_organismo ORDER BY p.monto_clp DESC) AS posicion
    FROM por_proveedor p
    JOIN totales t ON t.codigo_organismo = p.codigo_organismo
),
concentracion AS (
    SELECT codigo_organismo, round(sum(power(100 * monto_clp / monto_organismo, 2)), 0) AS hhi
    FROM ranking
    GROUP BY codigo_organismo
)
SELECT t.codigo_organismo, t.nombre_organismo, t.sector, '{mes}' AS mes,
       t.monto_clp, t.ordenes, t.proveedores,
       round(100 * t.monto_trato_directo_clp / t.monto_clp, 2) AS pct_monto_trato_directo,
       round(100 * t.monto_compra_agil_clp / t.monto_clp, 2) AS pct_monto_compra_agil,
       c.hhi,
       r.posicion, r.codigo_proveedor, r.nombre_proveedor, r.rut_proveedor,
       r.monto_clp AS monto_proveedor_clp, r.ordenes AS ordenes_proveedor,
       round(100 * r.monto_clp / t.monto_clp, 2) AS pct_proveedor
FROM totales t
JOIN concentracion c ON c.codigo_organismo = t.codigo_organismo
JOIN ranking r ON r.codigo_organismo = t.codigo_organismo
WHERE r.posicion <= 5
