resource "aws_vpc" "principal" {
  cidr_block = "10.20.0.0/16"
  tags       = { Name = "pdc-vpc" }
}

resource "aws_subnet" "privadas" {
  for_each          = { a = "10.20.1.0/24", b = "10.20.2.0/24" }
  vpc_id            = aws_vpc.principal.id
  cidr_block        = each.value
  availability_zone = "us-east-1${each.key}"
  tags              = { Name = "pdc-privada-${each.key}" }
}

resource "aws_security_group" "mwaa" {
  name   = "pdc-mwaa"
  vpc_id = aws_vpc.principal.id
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "mwaa" {
  bucket = "pdc-mwaa"
}

resource "aws_s3_object" "dags" {
  for_each = fileset("${path.module}/../../airflow/dags", "*.py")
  bucket   = aws_s3_bucket.mwaa.bucket
  key      = "dags/${each.value}"
  source   = "${path.module}/../../airflow/dags/${each.value}"
  etag     = filemd5("${path.module}/../../airflow/dags/${each.value}")
}

resource "aws_iam_role" "mwaa" {
  name = "pdc-mwaa-rol"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = ["airflow.amazonaws.com", "airflow-env.amazonaws.com"] } }]
  })
}

resource "aws_mwaa_environment" "principal" {
  name               = "pdc-airflow"
  airflow_version    = "2.10.5"
  environment_class  = "mw1.small"
  source_bucket_arn  = aws_s3_bucket.mwaa.arn
  dag_s3_path        = "dags"
  execution_role_arn = aws_iam_role.mwaa.arn
  network_configuration {
    security_group_ids = [aws_security_group.mwaa.id]
    subnet_ids         = [for s in aws_subnet.privadas : s.id]
  }
  airflow_configuration_options = {
    "core.default_timezone"  = "America/Santiago"
    "secrets.backend"        = "airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend"
    "secrets.backend_kwargs" = jsonencode({ connections_prefix = "airflow/connections", variables_prefix = "airflow/variables" })
  }
  depends_on = [aws_secretsmanager_secret_version.conexion_aws]
}

resource "aws_secretsmanager_secret" "conexion_aws" {
  name = "airflow/connections/aws_default"
}

resource "aws_secretsmanager_secret_version" "conexion_aws" {
  secret_id = aws_secretsmanager_secret.conexion_aws.id
  secret_string = jsonencode({
    conn_type = "aws"
    extra = {
      region_name    = "us-east-1"
      service_config = { glue = { endpoint_url = "http://glue-jobs:4567" } }
    }
  })
}
