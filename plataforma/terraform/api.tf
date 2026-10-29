variable "docdb_password" {
  type      = string
  sensitive = true
}

resource "aws_docdb_cluster" "api" {
  cluster_identifier  = "pdc-docdb"
  engine              = "docdb"
  master_username     = "pdc_admin"
  master_password     = var.docdb_password
  skip_final_snapshot = true
}

resource "aws_docdb_cluster_instance" "api" {
  identifier         = "pdc-docdb-1"
  cluster_identifier = aws_docdb_cluster.api.id
  instance_class     = "db.t3.medium"
}

resource "aws_secretsmanager_secret" "docdb" {
  name = "pdc/docdb"
}

resource "aws_secretsmanager_secret_version" "docdb" {
  secret_id = aws_secretsmanager_secret.docdb.id
  secret_string = jsonencode({
    host     = aws_docdb_cluster.api.endpoint
    port     = aws_docdb_cluster.api.port
    username = aws_docdb_cluster.api.master_username
    password = var.docdb_password
  })
}

data "archive_file" "api_compras" {
  type        = "zip"
  source_dir  = "${path.module}/.build/api_compras"
  output_path = "${path.module}/.build/api_compras.zip"
}

resource "aws_lambda_function" "api_compras" {
  function_name    = "pdc-api-compras"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "handler.handler"
  filename         = data.archive_file.api_compras.output_path
  source_code_hash = data.archive_file.api_compras.output_base64sha256
  timeout          = 30
  memory_size      = 256
  environment {
    variables = {
      SECRETO_DOCDB = aws_secretsmanager_secret.docdb.name
      HOST_DOCDB    = "floci-docdb-pdc-docdb"
      BASE_DOCDB    = "api_compras"
    }
  }
}

resource "aws_api_gateway_rest_api" "compras" {
  name        = "pdc-api-compras"
  description = "API de datos de compras públicas"
}

resource "aws_api_gateway_resource" "compras" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_rest_api.compras.root_resource_id
  path_part   = "compras"
}

resource "aws_api_gateway_resource" "organismos" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_resource.compras.id
  path_part   = "organismos"
}

resource "aws_api_gateway_resource" "organismo" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_resource.organismos.id
  path_part   = "{codigo}"
}

resource "aws_api_gateway_resource" "resumen" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_resource.organismo.id
  path_part   = "resumen"
}

resource "aws_api_gateway_resource" "alertas" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_resource.compras.id
  path_part   = "alertas"
}

resource "aws_api_gateway_resource" "concentracion" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  parent_id   = aws_api_gateway_resource.alertas.id
  path_part   = "concentracion"
}

locals {
  endpoints = {
    resumen       = aws_api_gateway_resource.resumen.id
    concentracion = aws_api_gateway_resource.concentracion.id
  }
}

resource "aws_api_gateway_method" "get" {
  for_each         = local.endpoints
  rest_api_id      = aws_api_gateway_rest_api.compras.id
  resource_id      = each.value
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "lambda" {
  for_each                = local.endpoints
  rest_api_id             = aws_api_gateway_rest_api.compras.id
  resource_id             = each.value
  http_method             = aws_api_gateway_method.get[each.key].http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.api_compras.invoke_arn
  lifecycle {
    ignore_changes = [timeout_milliseconds]
  }
}

resource "aws_api_gateway_deployment" "compras" {
  rest_api_id = aws_api_gateway_rest_api.compras.id
  triggers = {
    version = sha1(jsonencode([aws_api_gateway_method.get, aws_api_gateway_integration.lambda]))
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "v1" {
  rest_api_id   = aws_api_gateway_rest_api.compras.id
  deployment_id = aws_api_gateway_deployment.compras.id
  stage_name    = "v1"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "PermitirApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_compras.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.compras.execution_arn}/*/*"
}

resource "aws_api_gateway_usage_plan" "basico" {
  name = "pdc-plan-basico"
  api_stages {
    api_id = aws_api_gateway_rest_api.compras.id
    stage  = aws_api_gateway_stage.v1.stage_name
  }
  throttle_settings {
    rate_limit  = 10
    burst_limit = 20
  }
  quota_settings {
    limit  = 1000
    period = "DAY"
  }
}

output "url_api" {
  value = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.compras.id}/${aws_api_gateway_stage.v1.stage_name}/_user_request_"
}

output "id_plan_uso" {
  value = aws_api_gateway_usage_plan.basico.id
}
