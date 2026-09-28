from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.sensors.python import PythonSensor

ZONA = pendulum.timezone("America/Santiago")
BUCKET_RAW = "pdc-raw"
PREFIJO_RAW = "compras/ordenes_compra_masiva"
DIAS_MES_ANTERIOR = 5


# Meses que corresponde procesar según la fecha de ejecución
@task
def meses_a_procesar(data_interval_end=None):
    """Devuelve el mes en curso y, en los primeros días del mes, también el anterior."""
    hoy = data_interval_end.in_timezone(ZONA)
    meses = [hoy.format("YYYY-MM")]
    if hoy.day <= DIAS_MES_ANTERIOR:
        meses.insert(0, hoy.subtract(months=1).format("YYYY-MM"))
    return meses


# Chequeo de que raw tiene el archivo del día para cada mes
def raw_actualizado(meses, fecha):
    """Indica si el CSV de cada mes existe en raw y fue cargado en la fecha indicada o después."""
    s3 = S3Hook()
    for mes in meses:
        anio, numero = mes.split("-")
        clave = f"{PREFIJO_RAW}/mes={mes}/{anio}-{int(numero)}.csv"
        if not s3.check_for_key(clave, BUCKET_RAW):
            return False
        cargado = s3.get_key(clave, BUCKET_RAW).last_modified.astimezone(ZONA).date()
        if cargado < pendulum.parse(fecha).date():
            return False
    return True


with DAG(
    dag_id="dag_compras_diario",
    description="Procesa las órdenes de compra del día: raw → analytics → bodega",
    start_date=datetime(2026, 9, 1, tzinfo=ZONA),
    schedule="15 9 * * *",
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["compras", "glue"],
) as dag:
    meses = meses_a_procesar()

    esperar_raw = PythonSensor(
        task_id="esperar_raw_actualizado",
        python_callable=raw_actualizado,
        op_kwargs={"meses": meses, "fecha": "{{ data_interval_end.in_timezone('America/Santiago').to_date_string() }}"},
        mode="reschedule",
        poke_interval=600,
        timeout=3 * 3600,
    )

    items = GlueJobOperator.partial(
        task_id="glue_vw_ordenes_compra_items",
        job_name="pdc_vw_ordenes_compra_items",
        wait_for_completion=True,
        verbose=False,
        max_active_tis_per_dagrun=1,
    ).expand(script_args=meses.map(lambda mes: {"--fechaParticion": mes}))

    bodega = GlueJobOperator.partial(
        task_id="glue_dim_compras",
        job_name="pdc_dim_compras",
        wait_for_completion=True,
        verbose=False,
        max_active_tis_per_dagrun=1,
    ).expand(script_args=meses.map(lambda mes: {"--fechaParticion": mes}))

    meses >> esperar_raw >> items >> bodega
