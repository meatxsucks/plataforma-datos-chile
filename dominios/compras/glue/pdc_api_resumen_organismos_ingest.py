import sys
from datetime import datetime, timezone

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pymongo import ASCENDING, MongoClient
from pyspark.context import SparkContext

from glue_utils import obtener_secreto

args = getResolvedOptions(sys.argv, ["JOB_NAME", "fechaParticion", "bucketOrigen", "secretoDocdb", "hostDocdb", "baseDocdb"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

API = "resumen_organismos"
TAMANO_LOTE = 500
mes = args["fechaParticion"]
coleccion = f"{API}_{mes.replace('-', '_')}"
temporal = f"{coleccion}_carga"
secreto = obtener_secreto(args["secretoDocdb"])


# Conexión a DocumentDB a partir del secreto
def conectar():
    """Devuelve un cliente de DocumentDB con las credenciales del secreto."""
    return MongoClient(
        host=args["hostDocdb"] or secreto["host"],
        port=int(secreto["port"]),
        username=secreto["username"],
        password=secreto["password"],
        retryWrites=False,
    )


# Inserción de una partición en lotes
def insertar_particion(filas):
    """Inserta las filas de una partición en la colección temporal, en lotes."""
    cliente = conectar()
    destino = cliente[args["baseDocdb"]][temporal]
    lote = []
    for fila in filas:
        documento = fila.asDict(recursive=True)
        documento["_id"] = documento["codigo_organismo"]
        lote.append(documento)
        if len(lote) == TAMANO_LOTE:
            destino.insert_many(lote)
            lote = []
    if lote:
        destino.insert_many(lote)
    cliente.close()


documentos = spark.read.parquet(f"s3://{args['bucketOrigen']}/{API}/mes={mes}/")

cliente = conectar()
base = cliente[args["baseDocdb"]]
base[temporal].drop()
documentos.foreachPartition(insertar_particion)

cargados = base[temporal].count_documents({})
if cargados != documentos.count():
    raise RuntimeError(f"Se cargaron {cargados} documentos y se esperaban {documentos.count()}")

base[temporal].create_index([("sector", ASCENDING)])
base[temporal].create_index([("hhi", ASCENDING)])
cliente.admin.command("renameCollection", f"{args['baseDocdb']}.{temporal}", to=f"{args['baseDocdb']}.{coleccion}", dropTarget=True)
base["estado_api"].update_one(
    {"_id": API},
    {"$addToSet": {"meses": mes}, "$set": {"actualizado": datetime.now(timezone.utc)}},
    upsert=True,
)
cliente.close()

print(f"Colección {coleccion}: {cargados} documentos")
job.commit()
