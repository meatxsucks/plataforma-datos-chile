data "archive_file" "extractor_oc_masiva" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambdas/extractor_oc_masiva"
  output_path = "${path.module}/.build/extractor_oc_masiva.zip"
}

resource "aws_lambda_function" "extractor_oc_masiva" {
  function_name    = "pdc-extractor-oc-masiva"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.extractor_oc_masiva.output_path
  source_code_hash = data.archive_file.extractor_oc_masiva.output_base64sha256
  timeout          = 900
  memory_size      = 1024
  ephemeral_storage {
    size = 1024
  }
  environment {
    variables = { BUCKET_RAW = aws_s3_bucket.raw.bucket }
  }
}

resource "aws_iam_role" "scheduler" {
  name = "pdc-scheduler-rol"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "scheduler.amazonaws.com" } }]
  })
}

resource "aws_scheduler_schedule" "extractor_oc_masiva" {
  name                         = "pdc-extractor-oc-masiva-diario"
  schedule_expression          = "cron(0 9 * * ? *)"
  schedule_expression_timezone = "America/Santiago"
  flexible_time_window {
    mode = "OFF"
  }
  target {
    arn      = aws_lambda_function.extractor_oc_masiva.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({})
  }
}
