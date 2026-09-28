from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.analytics import Athena, Glue, GlueDataCatalog, KinesisDataStreams
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DocumentDB, Dynamodb, RDSPostgresqlInstance
from diagrams.aws.integration import EventbridgeScheduler
from diagrams.aws.management import AmazonManagedWorkflowsApacheAirflow, Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.security import IAM, SecretsManager
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.onprem.client import Users
from diagrams.onprem.iac import Terraform
from diagrams.programming.language import Python
from diagrams.saas.chat import Telegram

SALIDA = Path(__file__).parent / "arquitectura_general"

GRAFO = {
    "fontsize": "24",
    "fontname": "Helvetica-Bold",
    "labelloc": "t",
    "pad": "0.5",
    "nodesep": "0.9",
    "ranksep": "1.2",
    "splines": "ortho",
}
NODOS = {"fontsize": "12", "fontname": "Helvetica", "height": "1.3"}


# Estilo de un contenedor según el tipo de frontera de AWS
def estilo(borde, fondo="white", linea="solid"):
    """Devuelve los atributos Graphviz de un cluster con borde, fondo y tipo de línea."""
    return {
        "bgcolor": fondo,
        "pencolor": borde,
        "penwidth": "2",
        "style": linea,
        "fontname": "Helvetica-Bold",
        "fontsize": "14",
        "fontcolor": borde,
        "labeljust": "l",
        "margin": "20",
    }


NUBE = estilo("#232F3E")
CUENTA = estilo("#E7157B")
REGION = estilo("#00A4A6", linea="dashed")
GRUPO = estilo("#7D8998", fondo="#F7F9FA")
EXTERNO = estilo("#7D8998", fondo="#FFFFFF", linea="dashed")

BATCH = Edge(color="#1f6feb", penwidth="1.6")
STREAM = Edge(color="#d1242f", penwidth="2")
CONTROL = Edge(color="#7D8998", style="dashed")
GUIA = Edge(style="invis")

with Diagram(
    "Plataforma de Datos Chile",
    filename=str(SALIDA),
    outformat=["png", "svg"],
    direction="LR",
    show=False,
    graph_attr=GRAFO,
    node_attr=NODOS,
):
    with Cluster("Fuentes públicas", graph_attr=EXTERNO):
        gps = Users("Posiciones GPS\nDTPM / simulador")
        compras = Users("Mercado Público\nInfoLobby")
        economia = Users("Banco Central\nCMF · INE")

    with Cluster("AWS Cloud", graph_attr=NUBE):
        with Cluster("Cuenta 000000000000 · floci local", graph_attr=CUENTA):
            iam = IAM("IAM")

            with Cluster("Región us-east-1", graph_attr=REGION):
                with Cluster("Ingesta", graph_attr=GRUPO):
                    programador = EventbridgeScheduler("EventBridge\nScheduler")
                    extractor = Lambda("Lambdas\nextractoras")
                    kinesis = KinesisDataStreams("Kinesis\nposiciones")
                    consumidor = Lambda("Lambda\nconsumidora")

                with Cluster("Lago de datos · S3", graph_attr=GRUPO):
                    raw = SimpleStorageServiceS3Bucket("raw")
                    analytics = SimpleStorageServiceS3Bucket("stg · analytics")
                    sensible = SimpleStorageServiceS3Bucket("sensible\ndiccionario PII")

                with Cluster("Procesamiento", graph_attr=GRUPO):
                    glue = Glue("Glue PySpark")
                    catalogo = GlueDataCatalog("Glue Data\nCatalog")
                    athena = Athena("Athena")

                with Cluster("Almacenamiento de servicio", graph_attr=GRUPO):
                    bodega = RDSPostgresqlInstance("RDS Postgres\nbodega")
                    docdb = DocumentDB("DocumentDB\ngold")
                    dynamo = Dynamodb("DynamoDB\nestado actual")

                with Cluster("Exposición", graph_attr=GRUPO):
                    lectura = Lambda("Lambda\nde lectura")
                    gateway = APIGateway("API Gateway\nAPI keys")

                with Cluster("Orquestación y monitoreo", graph_attr=GRUPO):
                    mwaa = AmazonManagedWorkflowsApacheAirflow("MWAA\nAirflow")
                    secretos = SecretsManager("Secrets\nManager")
                    monitoreo = Cloudwatch("Monitoreo")
                    alertas = Lambda("Lambda\nalertas")

    with Cluster("Consumo", graph_attr=EXTERNO):
        clientes = Users("Consumidores\nde la API")
        tablero = Python("Streamlit")
        telegram = Telegram("Telegram")

    terraform = Terraform("Terraform")

    compras >> BATCH >> extractor
    economia >> BATCH >> extractor
    programador >> CONTROL >> extractor
    extractor >> BATCH >> raw
    gps >> STREAM >> kinesis >> STREAM >> consumidor
    consumidor >> STREAM >> dynamo

    raw >> BATCH >> glue
    glue >> BATCH >> analytics
    glue >> BATCH >> sensible
    glue >> CONTROL >> catalogo >> CONTROL >> athena
    analytics >> BATCH >> athena

    glue >> BATCH >> bodega
    glue >> BATCH >> docdb
    docdb >> BATCH >> lectura
    dynamo >> STREAM >> lectura
    lectura >> BATCH >> gateway >> BATCH >> clientes
    bodega >> BATCH >> tablero

    mwaa >> CONTROL >> glue
    secretos >> CONTROL >> glue
    glue >> CONTROL >> monitoreo >> CONTROL >> alertas >> CONTROL >> telegram
    terraform >> CONTROL >> iam
    raw >> GUIA >> analytics >> GUIA >> sensible
    bodega >> GUIA >> docdb >> GUIA >> dynamo
    mwaa >> GUIA >> secretos
