import os


# Lambda de prueba de la fase 1
def handler(event, context):
    """Devuelve el bucket raw configurado para confirmar que la Lambda corre en floci."""
    return {"ok": True, "bucket_raw": os.environ["BUCKET_RAW"]}
