from urllib.parse import urlparse

import boto3

TIPOS_HIVE = {
    "StringType": "string",
    "IntegerType": "int",
    "LongType": "bigint",
    "DoubleType": "double",
    "BooleanType": "boolean",
    "TimestampType": "timestamp",
    "DateType": "date",
}


# Spark SQL sobre vistas temporales
def spark_sql(spark, query, vistas):
    """Registra cada DataFrame como vista temporal con su nombre y ejecuta la query."""
    for nombre, df in vistas.items():
        df.createOrReplaceTempView(nombre)
    return spark.sql(query)


# Purga de una partición antes de reescribirla
def purgar_particion(ruta):
    """Borra todos los objetos bajo la ruta s3 indicada para que la escritura sea idempotente."""
    u = urlparse(ruta)
    bucket = boto3.resource("s3").Bucket(u.netloc)
    bucket.objects.filter(Prefix=u.path.lstrip("/")).delete()


# Tipo Hive de una columna Spark
def tipo_hive(tipo):
    """Traduce un tipo de Spark al tipo equivalente del catálogo de Glue."""
    nombre = type(tipo).__name__
    if nombre == "DecimalType":
        return f"decimal({tipo.precision},{tipo.scale})"
    return TIPOS_HIVE.get(nombre, "string")


# Alta o actualización de la tabla y su partición en el catálogo
def registrar_tabla(base, tabla, ruta, esquema, clave_particion, valor_particion):
    """Crea o actualiza la tabla Parquet en el catálogo de Glue y agrega la partición escrita."""
    glue = boto3.client("glue")
    columnas = [
        {"Name": c.name, "Type": tipo_hive(c.dataType)}
        for c in esquema.fields
        if c.name != clave_particion
    ]
    storage = {
        "Columns": columnas,
        "Location": ruta,
        "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
        "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
        "SerdeInfo": {"SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"},
    }
    tabla_input = {
        "Name": tabla,
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {"classification": "parquet"},
        "StorageDescriptor": storage,
        "PartitionKeys": [{"Name": clave_particion, "Type": "string"}],
    }
    try:
        glue.update_table(DatabaseName=base, TableInput=tabla_input)
    except glue.exceptions.EntityNotFoundException:
        glue.create_table(DatabaseName=base, TableInput=tabla_input)

    particion = {
        "Values": [valor_particion],
        "StorageDescriptor": {**storage, "Location": f"{ruta.rstrip('/')}/{clave_particion}={valor_particion}/"},
    }
    try:
        glue.create_partition(DatabaseName=base, TableName=tabla, PartitionInput=particion)
    except glue.exceptions.AlreadyExistsException:
        glue.update_partition(
            DatabaseName=base, TableName=tabla, PartitionValueList=[valor_particion], PartitionInput=particion
        )
