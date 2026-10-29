import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import lit

from glue_utils import ejecutar_sql, leer_sentencias, obtener_secreto, url_jdbc

args = getResolvedOptions(sys.argv, ["JOB_NAME", "fechaParticion", "bucketOrigen", "secretoBodega", "rutaSql", "hostBodega"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

mes = args["fechaParticion"]
secreto = obtener_secreto(args["secretoBodega"])
url = url_jdbc(secreto, args["hostBodega"] or None)

items = spark.read.parquet(f"s3://{args['bucketOrigen']}/vw_ordenes_compra_items/mes={mes}/").withColumn("mes", lit(mes))

items.write.jdbc(
    url=url,
    table="stage.oc_items",
    mode="overwrite",
    properties={"user": secreto["username"], "password": secreto["password"], "driver": "org.postgresql.Driver", "truncate": "true"},
)

sentencias = leer_sentencias(f"{args['rutaSql']}/02_cargar_compras.sql", mes=mes, fecha_efectiva=f"{mes}-01")
afectadas = ejecutar_sql(spark, url, secreto, sentencias)

print(f"Stage: {items.count()} filas | filas afectadas por sentencia: {afectadas}")
job.commit()
