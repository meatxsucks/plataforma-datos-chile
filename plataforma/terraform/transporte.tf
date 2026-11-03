variable "dtpm_usuario" {
  type      = string
  sensitive = true
}

variable "dtpm_clave" {
  type      = string
  sensitive = true
}

resource "aws_secretsmanager_secret" "dtpm" {
  name = "pdc/dtpm"
}

resource "aws_secretsmanager_secret_version" "dtpm" {
  secret_id     = aws_secretsmanager_secret.dtpm.id
  secret_string = jsonencode({ usuario = var.dtpm_usuario, clave = var.dtpm_clave })
}

resource "aws_kinesis_stream" "posiciones" {
  name        = "pdc-posiciones"
  shard_count = 1
}

resource "aws_dynamodb_table" "buses_actuales" {
  name         = "pdc-buses-actuales"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "patente"
  attribute {
    name = "patente"
    type = "S"
  }
}

data "archive_file" "productor_posiciones" {
  type        = "zip"
  source_dir  = "${path.module}/../../dominios/transporte/lambdas/productor_posiciones"
  output_path = "${path.module}/.build/productor_posiciones.zip"
}

resource "aws_lambda_function" "productor_posiciones" {
  function_name    = "pdc-productor-posiciones"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.productor_posiciones.output_path
  source_code_hash = data.archive_file.productor_posiciones.output_base64sha256
  timeout          = 90
  memory_size      = 512
  environment {
    variables = {
      STREAM       = aws_kinesis_stream.posiciones.name
      SECRETO_DTPM = aws_secretsmanager_secret.dtpm.name
    }
  }
}

data "archive_file" "consumidor_posiciones" {
  type        = "zip"
  source_dir  = "${path.module}/../../dominios/transporte/lambdas/consumidor_posiciones"
  output_path = "${path.module}/.build/consumidor_posiciones.zip"
}

resource "aws_lambda_function" "consumidor_posiciones" {
  function_name    = "pdc-consumidor-posiciones"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.consumidor_posiciones.output_path
  source_code_hash = data.archive_file.consumidor_posiciones.output_base64sha256
  timeout          = 60
  memory_size      = 512
  environment {
    variables = {
      TABLA      = aws_dynamodb_table.buses_actuales.name
      BUCKET_RAW = aws_s3_bucket.raw.bucket
    }
  }
}

resource "aws_lambda_event_source_mapping" "posiciones" {
  event_source_arn  = aws_kinesis_stream.posiciones.arn
  function_name     = aws_lambda_function.consumidor_posiciones.arn
  starting_position = "LATEST"
  batch_size        = 500
}

resource "aws_scheduler_schedule" "productor_posiciones" {
  name                = "pdc-productor-posiciones-minuto"
  schedule_expression = "rate(1 minute)"
  state               = "DISABLED"
  flexible_time_window {
    mode = "OFF"
  }
  target {
    arn      = aws_lambda_function.productor_posiciones.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({})
  }
}

data "archive_file" "api_transporte" {
  type        = "zip"
  source_dir  = "${path.module}/../../dominios/transporte/lambdas/api_transporte"
  output_path = "${path.module}/.build/api_transporte.zip"
}

resource "aws_lambda_function" "api_transporte" {
  function_name    = "pdc-api-transporte"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.api_transporte.output_path
  source_code_hash = data.archive_file.api_transporte.output_base64sha256
  timeout          = 30
  memory_size      = 256
  environment {
    variables = { TABLA = aws_dynamodb_table.buses_actuales.name }
  }
}

resource "aws_api_gateway_resource" "transporte" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_rest_api.compras.root_resource_id
  path_part   = "transporte"
}

resource "aws_api_gateway_resource" "transporte_buses" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_resource.transporte.id
  path_part   = "buses"
}

resource "aws_api_gateway_method" "transporte_buses" {
  rest_api_id      = aws_api_gateway_rest_api.compras.id
  resource_id      = aws_api_gateway_resource.transporte_buses.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "transporte_buses" {
  rest_api_id             = aws_api_gateway_rest_api.compras.id
  resource_id             = aws_api_gateway_resource.transporte_buses.id
  http_method             = aws_api_gateway_method.transporte_buses.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.api_transporte.invoke_arn
  lifecycle {
    ignore_changes = [timeout_milliseconds]
  }
}

resource "aws_lambda_permission" "api_gateway_transporte" {
  statement_id  = "PermitirApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_transporte.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.compras.execution_arn}/*/*"
}
