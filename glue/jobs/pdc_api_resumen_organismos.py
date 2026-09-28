import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

from glue_utils import leer_sentencias, obtener_secreto, purgar_particion, spark_sql, url_jdbc

args = getResolvedOptions(sys.argv, ["JOB_NAME", "fechaParticion", "bucketDestino", "secretoBodega", "rutaSql", "hostBodega"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

API = "resumen_organismos"
mes = args["fechaParticion"]
destino = f"s3://{args['bucketDestino']}/{API}/mes={mes}/"
secreto = obtener_secreto(args["secretoBodega"])

consulta = leer_sentencias(f"{args['rutaSql']}/{API}.sql", mes=mes)[0]
filas = spark.read.jdbc(
    url=url_jdbc(secreto, args["hostBodega"] or None),
    table=f"({consulta}) AS resumen",
    properties={"user": secreto["username"], "password": secreto["password"], "driver": "org.postgresql.Driver"},
)

documentos = spark_sql(
    spark,
    """
    SELECT codigo_organismo, max(nombre_organismo) AS nombre_organismo, max(sector) AS sector, max(mes) AS mes,
           CAST(max(monto_clp) AS DOUBLE) AS monto_clp, max(ordenes) AS ordenes, max(proveedores) AS proveedores,
           CAST(max(pct_monto_trato_directo) AS DOUBLE) AS pct_monto_trato_directo,
           CAST(max(pct_monto_compra_agil) AS DOUBLE) AS pct_monto_compra_agil,
           CAST(max(hhi) AS INT) AS hhi,
           sort_array(collect_list(struct(
               CAST(posicion AS INT) AS posicion, codigo_proveedor, nombre_proveedor, rut_proveedor,
               CAST(monto_proveedor_clp AS DOUBLE) AS monto_clp, ordenes_proveedor AS ordenes,
               CAST(pct_proveedor AS DOUBLE) AS pct_monto
           ))) AS principales_proveedores
    FROM filas
    GROUP BY codigo_organismo
    """,
    {"filas": filas},
)

purgar_particion(destino)
documentos.coalesce(1).write.mode("overwrite").parquet(destino)

print(f"Organismos: {documentos.count()}")
job.commit()
