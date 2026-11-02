variable "openrouter_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "openrouter_modelo" {
  type    = string
  default = "openrouter/free"
}

data "archive_file" "monitoreo" {
  type        = "zip"
  source_dir  = "${path.module}/.build/monitoreo"
  output_path = "${path.module}/.build/monitoreo.zip"
}

resource "aws_lambda_function" "monitoreo" {
  function_name    = "pdc-monitoreo"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "handler.handler"
  filename         = data.archive_file.monitoreo.output_path
  source_code_hash = data.archive_file.monitoreo.output_base64sha256
  timeout          = 60
  memory_size      = 256
  environment {
    variables = {
      BUCKET_RAW         = aws_s3_bucket.raw.bucket
      SECRETO_BODEGA     = aws_secretsmanager_secret.bodega.name
      HOST_BODEGA        = "floci"
      OPENROUTER_API_KEY = var.openrouter_api_key
      OPENROUTER_MODELO  = var.openrouter_modelo
    }
  }
}
