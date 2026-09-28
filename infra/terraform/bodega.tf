variable "postgres_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "bodega" {
  identifier          = "pdc-bodega"
  engine              = "postgres"
  engine_version      = "16"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  db_name             = "bodega"
  username            = "pdc_admin"
  password            = var.postgres_password
  skip_final_snapshot = true
}

resource "aws_secretsmanager_secret" "bodega" {
  name = "pdc/bodega"
}

resource "aws_secretsmanager_secret_version" "bodega" {
  secret_id = aws_secretsmanager_secret.bodega.id
  secret_string = jsonencode({
    host     = aws_db_instance.bodega.address
    port     = aws_db_instance.bodega.port
    dbname   = aws_db_instance.bodega.db_name
    username = aws_db_instance.bodega.username
    password = var.postgres_password
  })
}
