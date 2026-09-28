import sys

from awsglue import DynamicFrame
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

from glue_utils import (
    purgar_particion,
    registrar_tabla,
    spark_sql,
    sql_decimal,
    sql_es_persona_natural,
    sql_token_rut,
)

args = getResolvedOptions(sys.argv, ["JOB_NAME", "fechaParticion", "bucketOrigen", "bucketDestino", "bucketSensible", "baseDatos", "claveSeudonimo"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

TABLA = "vw_ordenes_compra_items"
mes = args["fechaParticion"]
origen = f"s3://{args['bucketOrigen']}/compras/ordenes_compra_masiva/mes={mes}/"
destino = f"s3://{args['bucketDestino']}/{TABLA}/"
diccionario = f"s3://{args['bucketSensible']}/dicc_proveedor_persona_masiva/"

raw = spark.read.options(
    header=True, sep=";", quote='"', escape='"', multiLine=True, encoding="ISO-8859-1"
).csv(origen)

query_base = f"""
SELECT *,
       {sql_es_persona_natural('rut_proveedor')} AS es_persona_natural,
       {sql_token_rut('rut_proveedor', args['claveSeudonimo'])} AS token_proveedor
FROM (
    SELECT CAST(IDItem AS BIGINT) AS id_item,
           CAST(ID AS BIGINT) AS id_orden,
           Codigo AS codigo,
           Nombre AS nombre,
           Tipo AS tipo,
           EsTratoDirecto = 'Si' AS es_trato_directo,
           EsCompraAgil = 'Si' AS es_compra_agil,
           CAST(codigoEstado AS INT) AS codigo_estado,
           Estado AS estado,
           to_date(FechaCreacion) AS fecha_creacion,
           to_date(FechaEnvio) AS fecha_envio,
           to_date(FechaAceptacion) AS fecha_aceptacion,
           to_date(fechaUltimaModificacion) AS fecha_ultima_modificacion,
           TipoMonedaOC AS moneda_oc,
           {sql_decimal('MontoTotalOC')} AS monto_total_oc,
           {sql_decimal('MontoTotalOC_PesosChilenos')} AS monto_total_oc_clp,
           {sql_decimal('TotalNetoOC')} AS total_neto_oc,
           {sql_decimal('PorcentajeIva', 'DECIMAL(5,2)')} AS porcentaje_iva,
           CodigoOrganismoPublico AS codigo_organismo,
           OrganismoPublico AS nombre_organismo,
           sector,
           RutUnidadCompra AS rut_unidad,
           CodigoUnidadCompra AS codigo_unidad,
           UnidadCompra AS nombre_unidad,
           trim(RegionUnidadCompra) AS region_unidad,
           CodigoProveedor AS codigo_proveedor,
           NombreProveedor AS nombre_proveedor,
           RutSucursal AS rut_proveedor,
           ActividadProveedor AS actividad_proveedor,
           trim(RegionProveedor) AS region_proveedor,
           NULLIF(CodigoLicitacion, '') AS codigo_licitacion,
           NULLIF(Codigo_ConvenioMarco, '') AS codigo_convenio_marco,
           codigoProductoONU AS codigo_producto_onu,
           NombreroductoGenerico AS producto_generico,
           RubroN1 AS rubro_n1,
           RubroN2 AS rubro_n2,
           RubroN3 AS rubro_n3,
           {sql_decimal('cantidad')} AS cantidad,
           UnidadMedida AS unidad_medida,
           monedaItem AS moneda_item,
           {sql_decimal('precioNeto')} AS precio_neto,
           {sql_decimal('totalLineaNeto')} AS total_linea_neto,
           ROW_NUMBER() OVER (PARTITION BY IDItem ORDER BY fechaUltimaModificacion DESC) AS rn
    FROM raw
    WHERE IDItem IS NOT NULL
) t
WHERE rn = 1
"""
base = spark_sql(spark, query_base, {"raw": raw}).drop("rn")
base.cache()

columnas = ", ".join(c for c in base.columns if c not in ("nombre_proveedor", "rut_proveedor", "token_proveedor"))
resultado = spark_sql(
    spark,
    f"""
    SELECT {columnas},
           CASE WHEN es_persona_natural THEN 'PERSONA NATURAL' ELSE nombre_proveedor END AS nombre_proveedor,
           CASE WHEN es_persona_natural THEN token_proveedor ELSE rut_proveedor END AS rut_proveedor,
           '{mes}' AS mes
    FROM base
    """,
    {"base": base},
)

dicc = spark_sql(
    spark,
    "SELECT DISTINCT token_proveedor, rut_proveedor, nombre_proveedor FROM base WHERE es_persona_natural",
    {"base": base},
)

purgar_particion(f"{destino}mes={mes}/")
glueContext.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(resultado.repartition("mes"), glueContext, "resultado"),
    connection_type="s3",
    format="glueparquet",
    connection_options={"path": destino, "partitionKeys": ["mes"]},
    format_options={"compression": "snappy"},
    transformation_ctx="escritura",
)
registrar_tabla(args["baseDatos"], TABLA, destino, resultado.schema, "mes", mes)

purgar_particion(f"{diccionario}mes={mes}/")
dicc.coalesce(1).write.mode("overwrite").parquet(f"{diccionario}mes={mes}/")

print(f"Items únicos: {base.count()} | personas naturales en diccionario: {dicc.count()}")
job.commit()
