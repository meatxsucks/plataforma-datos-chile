import sys

from awsglue import DynamicFrame
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

from glue_utils import purgar_particion, registrar_tabla, spark_sql

args = getResolvedOptions(sys.argv, ["JOB_NAME", "fechaParticion", "bucketOrigen", "bucketDestino", "bucketSensible", "baseDatos", "claveSeudonimo"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

TABLA = "vw_ordenes_compra"
fecha = args["fechaParticion"]
origen = f"s3://{args['bucketOrigen']}/compras/ordenes_compra/fecha_carga={fecha}/"
destino = f"s3://{args['bucketDestino']}/{TABLA}/"
diccionario = f"s3://{args['bucketSensible']}/dicc_proveedor_persona/"

raw = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    format="json",
    connection_options={"paths": [origen]},
    transformation_ctx="raw",
).toDF()

query_base = f"""
SELECT *,
       CAST(split(replace(rut_proveedor, '.', ''), '-')[0] AS BIGINT) < 50000000 AS es_persona_natural,
       sha2(concat('{args['claveSeudonimo']}', regexp_replace(upper(rut_proveedor), '[^0-9K]', '')), 256) AS token_proveedor
FROM (
    SELECT Codigo AS codigo,
           Nombre AS nombre,
           CAST(CodigoEstado AS INT) AS codigo_estado,
           Estado AS estado,
           NULLIF(CodigoLicitacion, '') AS codigo_licitacion,
           Tipo AS tipo,
           TipoMoneda AS moneda,
           to_timestamp(Fechas.FechaCreacion) AS fecha_creacion,
           to_timestamp(Fechas.FechaEnvio) AS fecha_envio,
           to_timestamp(Fechas.FechaAceptacion) AS fecha_aceptacion,
           to_timestamp(CAST(Fechas.FechaCancelacion AS STRING)) AS fecha_cancelacion,
           to_timestamp(Fechas.FechaUltimaModificacion) AS fecha_ultima_modificacion,
           CAST(TotalNeto AS DECIMAL(18,2)) AS total_neto,
           CAST(PorcentajeIva AS DECIMAL(5,2)) AS porcentaje_iva,
           CAST(Impuestos AS DECIMAL(18,2)) AS impuestos,
           CAST(Total AS DECIMAL(18,2)) AS total,
           Comprador.CodigoOrganismo AS codigo_organismo,
           Comprador.NombreOrganismo AS nombre_organismo,
           Comprador.RutUnidad AS rut_unidad,
           Comprador.CodigoUnidad AS codigo_unidad,
           Comprador.NombreUnidad AS nombre_unidad,
           Comprador.RegionUnidad AS region_unidad,
           Comprador.ComunaUnidad AS comuna_unidad,
           Proveedor.Codigo AS codigo_proveedor,
           Proveedor.Nombre AS nombre_proveedor,
           Proveedor.RutSucursal AS rut_proveedor,
           Proveedor.Actividad AS actividad_proveedor,
           NULLIF(Proveedor.Region, '') AS region_proveedor,
           CAST(Items.Cantidad AS INT) AS cantidad_items,
           ROW_NUMBER() OVER (PARTITION BY Codigo ORDER BY Fechas.FechaUltimaModificacion DESC) AS rn
    FROM raw
) t
WHERE rn = 1
"""
base = spark_sql(spark, query_base, {"raw": raw})

resultado = spark_sql(
    spark,
    f"""
    SELECT codigo, nombre, codigo_estado, estado, codigo_licitacion, tipo, moneda,
           fecha_creacion, fecha_envio, fecha_aceptacion, fecha_cancelacion, fecha_ultima_modificacion,
           total_neto, porcentaje_iva, impuestos, total,
           codigo_organismo, nombre_organismo, rut_unidad, codigo_unidad, nombre_unidad, region_unidad, comuna_unidad,
           codigo_proveedor,
           CASE WHEN es_persona_natural THEN 'PERSONA NATURAL' ELSE nombre_proveedor END AS nombre_proveedor,
           CASE WHEN es_persona_natural THEN token_proveedor ELSE rut_proveedor END AS rut_proveedor,
           es_persona_natural, actividad_proveedor, region_proveedor,
           cantidad_items, '{fecha}' AS fecha
    FROM base
    """,
    {"base": base},
)

dicc = spark_sql(
    spark,
    "SELECT DISTINCT token_proveedor, rut_proveedor, nombre_proveedor FROM base WHERE es_persona_natural",
    {"base": base},
)

purgar_particion(f"{destino}fecha={fecha}/")
glueContext.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(resultado.repartition("fecha"), glueContext, "resultado"),
    connection_type="s3",
    format="glueparquet",
    connection_options={"path": destino, "partitionKeys": ["fecha"]},
    format_options={"compression": "snappy"},
    transformation_ctx="escritura",
)
registrar_tabla(args["baseDatos"], TABLA, destino, resultado.schema, "fecha", fecha)

purgar_particion(f"{diccionario}fecha={fecha}/")
dicc.coalesce(1).write.mode("overwrite").parquet(f"{diccionario}fecha={fecha}/")

print(f"Registros leídos: {raw.count()} | escritos: {resultado.count()} | personas naturales en diccionario: {dicc.count()}")
job.commit()
