resource "aws_s3_bucket" "capas" {
  for_each = toset(["stg", "analytics", "cert", "sensible", "athena-resultados"])
  bucket   = "pdc-${each.key}"
}

resource "aws_glue_catalog_database" "pdc" {
  name = "pdc"
}
