import json
import os
import shlex
import threading
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import boto3
import docker

FLOCI = os.environ.get("FLOCI_URL", "http://floci:4566")
IMAGEN = os.environ.get("GLUE_IMAGEN", "public.ecr.aws/glue/aws-glue-libs:5")
RED = os.environ.get("RED_DOCKER", "plataforma-datos-chile_default")
VOLUMEN = os.environ.get("VOLUMEN_TRABAJO", "pdc-glue-trabajo")
TRABAJO = Path("/trabajo")
MEMORIA_DRIVER = os.environ.get("MEMORIA_DRIVER", "3g")
PARTICIONES_SHUFFLE = os.environ.get("PARTICIONES_SHUFFLE", "16")
ARGUMENTOS_INTERNOS = ("--extra-py-files", "--additional-python-modules", "--job-language", "--enable-", "--TempDir", "--job-bookmark-option")

glue = boto3.client("glue", endpoint_url=FLOCI)
s3 = boto3.client("s3", endpoint_url=FLOCI)
motor = docker.from_env()
ejecuciones = {}


# Hora actual en segundos epoch, como la devuelve la API de Glue
def ahora():
    """Devuelve la hora UTC actual en segundos epoch."""
    return datetime.now(timezone.utc).timestamp()


# Descarga de un archivo de S3 al directorio de la ejecución
def descargar(ruta_s3, destino):
    """Descarga un objeto s3:// al directorio indicado y devuelve la ruta local."""
    u = urlparse(ruta_s3)
    local = destino / Path(u.path).name
    s3.download_file(u.netloc, u.path.lstrip("/"), str(local))
    return local


# Comando spark-submit para una ejecución
def armar_comando(script, py_files, argumentos, nombre_job):
    """Arma el spark-submit con la configuración S3A de floci y los argumentos del job."""
    comando = [
        "spark-submit",
        "--driver-memory", MEMORIA_DRIVER,
        "--conf", f"spark.sql.shuffle.partitions={PARTICIONES_SHUFFLE}",
        "--conf", "spark.hadoop.fs.s3.impl=org.apache.hadoop.fs.s3a.S3AFileSystem",
        "--conf", f"spark.hadoop.fs.s3a.endpoint={FLOCI}",
        "--conf", "spark.hadoop.fs.s3a.path.style.access=true",
        "--conf", "spark.hadoop.fs.s3a.connection.ssl.enabled=false",
        "--conf", "spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        "--conf", "spark.hadoop.fs.s3a.access.key=test",
        "--conf", "spark.hadoop.fs.s3a.secret.key=test",
    ]
    if py_files:
        comando += ["--py-files", ",".join(py_files)]
    comando += [script, "--JOB_NAME", nombre_job]
    for clave, valor in argumentos.items():
        comando += [clave, valor]
    return comando


# Ejecución de un job en un contenedor de Glue
def ejecutar(id_ejecucion, nombre_job, argumentos_run):
    """Descarga script y dependencias del job, corre el contenedor de Glue y registra el resultado."""
    registro = ejecuciones[id_ejecucion]
    try:
        job = glue.get_job(JobName=nombre_job)["Job"]
        directorio = TRABAJO / id_ejecucion
        directorio.mkdir(parents=True)
        argumentos = {**job.get("DefaultArguments", {}), **argumentos_run}
        script = descargar(job["Command"]["ScriptLocation"], directorio)
        py_files = [descargar(r, directorio) for r in argumentos.get("--extra-py-files", "").split(",") if r]
        propios = {k: v for k, v in argumentos.items() if not k.startswith(ARGUMENTOS_INTERNOS)}

        comando = shlex.join(armar_comando(f"/trabajo/{id_ejecucion}/{script.name}", [f"/trabajo/{id_ejecucion}/{p.name}" for p in py_files], propios, nombre_job))
        modulos = [m for m in argumentos.get("--additional-python-modules", "").split(",") if m]
        if modulos:
            comando = f"pip install --quiet --user {shlex.join(modulos)} && {comando}"

        registro["JobRunState"] = "RUNNING"
        contenedor = motor.containers.run(
            IMAGEN,
            [comando],
            entrypoint=["bash", "-c"],
            volumes={VOLUMEN: {"bind": "/trabajo", "mode": "rw"}},
            network=RED,
            environment={
                "AWS_ACCESS_KEY_ID": "test",
                "AWS_SECRET_ACCESS_KEY": "test",
                "AWS_REGION": "us-east-1",
                "AWS_DEFAULT_REGION": "us-east-1",
                "AWS_ENDPOINT_URL": FLOCI,
            },
            name=f"pdc-glue-{nombre_job}-{id_ejecucion[:8]}",
            detach=True,
        )
        salida = contenedor.wait()
        logs = contenedor.logs().decode(errors="ignore").splitlines()
        contenedor.remove()
        (directorio / "salida.log").write_text("\n".join(logs))
        registro["JobRunState"] = "SUCCEEDED" if salida["StatusCode"] == 0 else "FAILED"
        if salida["StatusCode"] != 0:
            causa = "sin memoria: el proceso fue terminado por el sistema (código 137)" if salida["StatusCode"] == 137 else f"código de salida {salida['StatusCode']}"
            detalle = "\n".join(l for l in logs[-40:] if "Error" in l or "Exception" in l)
            registro["ErrorMessage"] = f"{causa}\n{detalle}"[-2000:]
    except Exception as e:
        registro["JobRunState"] = "FAILED"
        registro["ErrorMessage"] = str(e)[:2000]
    registro["CompletedOn"] = ahora()
    registro["ExecutionTime"] = int(registro["CompletedOn"] - registro["StartedOn"])


# Reenvío de una operación a floci
def reenviar(cuerpo, cabeceras):
    """Reenvía la petición original a floci y devuelve su código y cuerpo."""
    peticion = urllib.request.Request(FLOCI + "/", data=cuerpo, headers={k: v for k, v in cabeceras.items() if k.lower() != "host"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class Manejador(BaseHTTPRequestHandler):
    """Atiende la API JSON 1.1 de Glue: ejecuta las operaciones de jobs y reenvía el resto a floci."""

    def responder(self, codigo, cuerpo):
        self.send_response(codigo)
        self.send_header("Content-Type", "application/x-amz-json-1.1")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        crudo = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        operacion = self.headers.get("X-Amz-Target", "").split(".")[-1]
        datos = json.loads(crudo or b"{}")

        if operacion == "StartJobRun":
            id_ejecucion = "jr_" + uuid.uuid4().hex
            ejecuciones[id_ejecucion] = {
                "Id": id_ejecucion,
                "JobName": datos["JobName"],
                "JobRunState": "STARTING",
                "StartedOn": ahora(),
                "Arguments": datos.get("Arguments", {}),
                "Attempt": 0,
            }
            threading.Thread(target=ejecutar, args=(id_ejecucion, datos["JobName"], datos.get("Arguments", {})), daemon=True).start()
            return self.responder(200, json.dumps({"JobRunId": id_ejecucion}).encode())

        if operacion == "GetJobRun":
            registro = ejecuciones.get(datos["RunId"])
            if not registro:
                return self.responder(400, json.dumps({"__type": "EntityNotFoundException", "Message": "Ejecución no encontrada"}).encode())
            return self.responder(200, json.dumps({"JobRun": registro}).encode())

        if operacion == "GetJobRuns":
            propias = [r for r in ejecuciones.values() if r["JobName"] == datos["JobName"]]
            return self.responder(200, json.dumps({"JobRuns": sorted(propias, key=lambda r: -r["StartedOn"])}).encode())

        codigo, cuerpo = reenviar(crudo, dict(self.headers))
        return self.responder(codigo, cuerpo)

    def log_message(self, formato, *args):
        print(f"{self.headers.get('X-Amz-Target', '-')} {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 4567), Manejador).serve_forever()
