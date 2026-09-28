resource "aws_s3_bucket" "raw" {
  bucket = "pdc-raw"
}

resource "aws_iam_role" "lambda" {
  name = "pdc-lambda-rol"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

data "archive_file" "hola" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambdas/hola"
  output_path = "${path.module}/.build/hola.zip"
}

resource "aws_lambda_function" "hola" {
  function_name    = "pdc-hola"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.hola.output_path
  source_code_hash = data.archive_file.hola.output_base64sha256
  environment {
    variables = { BUCKET_RAW = aws_s3_bucket.raw.bucket }
  }
}
