variable "clave_seudonimo" {
  type      = string
  sensitive = true
}

resource "aws_s3_bucket" "glue_assets" {
  bucket = "pdc-glue-assets"
}

locals {
  archivos_glue = merge(
    { for f in fileset("${path.module}/../../glue/jobs", "*.py") : "jobs/${f}" => "${path.module}/../../glue/jobs/${f}" },
    { for f in fileset("${path.module}/../../sql/bodega", "*.sql") : "sql/bodega/${f}" => "${path.module}/../../sql/bodega/${f}" },
    { "utils/glue_utils.py" = "${path.module}/../../utils/glue_utils.py" },
  )
  ruta_assets = "s3://${aws_s3_bucket.glue_assets.bucket}"
  argumentos_comunes = {
    "--extra-py-files" = "${local.ruta_assets}/utils/glue_utils.py"
    "--job-language"   = "python"
  }
  jobs = {
    pdc_vw_ordenes_compra_items = {
      "--bucketOrigen"     = aws_s3_bucket.raw.bucket
      "--bucketDestino"    = aws_s3_bucket.capas["analytics"].bucket
      "--bucketSensible"   = aws_s3_bucket.capas["sensible"].bucket
      "--baseDatos"        = aws_glue_catalog_database.pdc.name
      "--secretoSeudonimo" = aws_secretsmanager_secret.seudonimo.name
    }
    pdc_dim_compras = {
      "--bucketOrigen"  = aws_s3_bucket.capas["analytics"].bucket
      "--secretoBodega" = aws_secretsmanager_secret.bodega.name
      "--rutaSql"       = "${local.ruta_assets}/sql/bodega"
      "--hostBodega"    = "floci"
    }
  }
}

resource "aws_s3_object" "glue_assets" {
  for_each = local.archivos_glue
  bucket   = aws_s3_bucket.glue_assets.bucket
  key      = each.key
  source   = each.value
  etag     = filemd5(each.value)
}

resource "aws_secretsmanager_secret" "seudonimo" {
  name = "pdc/seudonimo"
}

resource "aws_secretsmanager_secret_version" "seudonimo" {
  secret_id     = aws_secretsmanager_secret.seudonimo.id
  secret_string = jsonencode({ clave = var.clave_seudonimo })
}

resource "aws_iam_role" "glue" {
  name = "pdc-glue-rol"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "glue.amazonaws.com" } }]
  })
}

resource "aws_glue_job" "jobs" {
  for_each          = local.jobs
  name              = each.key
  role_arn          = aws_iam_role.glue.arn
  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  command {
    name            = "glueetl"
    script_location = "${local.ruta_assets}/jobs/${each.key}.py"
    python_version  = "3"
  }
  default_arguments = merge(local.argumentos_comunes, each.value)
  depends_on        = [aws_s3_object.glue_assets]
}
