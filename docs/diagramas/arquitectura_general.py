from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.analytics import Athena, Glue, GlueDataCatalog, KinesisDataStreams
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DocumentDB, Dynamodb, RDSPostgresqlInstance
from diagrams.aws.integration import EventbridgeScheduler
from diagrams.aws.management import AmazonManagedWorkflowsApacheAirflow, Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.security import SecretsManager
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.onprem.client import Users
from diagrams.onprem.iac import Terraform
from diagrams.programming.language import Python
from diagrams.saas.chat import Telegram
from diagrams.generic.blank import Blank

SALIDA = Path(__file__).parent / "arquitectura_general"

ATRIBUTOS = {
    "fontsize": "22",
    "fontname": "Helvetica",
    "labelloc": "t",
    "pad": "0.6",
    "nodesep": "0.7",
    "ranksep": "1.1",
    "splines": "spline",
}
NODOS = {"fontsize": "12", "fontname": "Helvetica"}
BATCH = Edge(color="#1f6feb")
STREAM = Edge(color="#d1242f", style="bold")
CONTROL = Edge(color="#8c959f", style="dashed")
INVISIBLE = Edge(style="invis")

with Diagram(
    "Plataforma de Datos Chile — AWS emulado con floci",
    filename=str(SALIDA),
    outformat=["png", "svg"],
    direction="LR",
    show=False,
    graph_attr=ATRIBUTOS,
    node_attr=NODOS,
):
    with Cluster("Fuentes públicas"):
        mp = Users("Mercado Público\nInfoLobby")
        eco = Users("Banco Central\nCMF · INE")
        gps = Users("Posiciones GPS\n(DTPM / simulador)")

    with Cluster("Ingesta"):
        programador = EventbridgeScheduler("EventBridge")
        extractor = Lambda("Lambdas\nextractoras")
        stream = KinesisDataStreams("Kinesis\nposiciones")
        consumidor = Lambda("Lambda\nconsumidora")

    with Cluster("Lago de datos (S3)"):
        raw = SimpleStorageServiceS3Bucket("raw")
        stg = SimpleStorageServiceS3Bucket("stg")
        analytics = SimpleStorageServiceS3Bucket("analytics")
        sensible = SimpleStorageServiceS3Bucket("sensible\n(diccionario PII)")

    with Cluster("Procesamiento"):
        glue = Glue("Glue PySpark\nvw · cert · dim · api")
        catalogo = GlueDataCatalog("Catálogo")
        athena = Athena("Athena")

    with Cluster("Servicio"):
        bodega = RDSPostgresqlInstance("Bodega\nPostgres")
        docdb = DocumentDB("DocumentDB\n(gold)")
        estado = Dynamodb("DynamoDB\nestado actual")
        api_lambda = Lambda("Lambda\nde lectura")
        gateway = APIGateway("API Gateway\nAPI keys")
        tablero = Python("Streamlit")

    with Cluster("Operación y gobernanza"):
        airflow = AmazonManagedWorkflowsApacheAirflow("MWAA\nAirflow")
        monitoreo = Cloudwatch("Monitoreo\nfrescura · volumen")
        alertas = Telegram("Alertas\n+ OpenRouter")
        secretos = SecretsManager("Secretos")
        iac = Terraform("Terraform")
        gobierno = Blank("OpenMetadata\nGreat Expectations")

    programador >> CONTROL >> extractor
    [mp, eco] >> BATCH >> extractor >> BATCH >> raw
    gps >> STREAM >> stream >> STREAM >> consumidor
    consumidor >> STREAM >> estado
    consumidor >> STREAM >> raw

    raw >> BATCH >> glue
    glue >> BATCH >> stg
    glue >> BATCH >> analytics
    glue >> BATCH >> sensible
    raw >> INVISIBLE >> stg >> INVISIBLE >> analytics >> INVISIBLE >> sensible
    glue >> CONTROL >> catalogo
    analytics >> BATCH >> athena
    catalogo >> CONTROL >> athena
    glue >> BATCH >> bodega
    glue >> BATCH >> docdb
    bodega >> BATCH >> tablero
    [docdb, estado] >> BATCH >> api_lambda >> BATCH >> gateway

    airflow >> CONTROL >> glue
    glue >> CONTROL >> monitoreo >> CONTROL >> alertas
    iac >> INVISIBLE >> secretos >> INVISIBLE >> airflow
    monitoreo >> INVISIBLE >> gobierno
