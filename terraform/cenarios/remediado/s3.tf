# Cenário de demonstração: cópia do terraform/aws/s3.tf com as remediações aplicadas.
# Mudanças marcadas com "REMEDIADO".

resource "aws_s3_bucket" "relatorios_financeiros" {
  bucket = "acme-relatorios-financeiros-prd"

  tags = {
    Ambiente = "producao"
    Sistema  = "financeiro"
  }
}

resource "aws_s3_bucket_public_access_block" "relatorios_financeiros" {
  bucket = aws_s3_bucket.relatorios_financeiros.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "relatorios_financeiros" {
  bucket = aws_s3_bucket.relatorios_financeiros.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = "arn:aws:kms:sa-east-1:111122223333:key/1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "relatorios_financeiros" {
  bucket = aws_s3_bucket.relatorios_financeiros.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "exportacao_clientes" {
  bucket = "acme-exportacao-clientes-crm"

  tags = {
    Ambiente = "producao"
    Sistema  = "crm"
  }
}

# REMEDIADO: as 4 travas passaram de false para true.
resource "aws_s3_bucket_public_access_block" "exportacao_clientes" {
  bucket = aws_s3_bucket.exportacao_clientes.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# REMEDIADO: a bucket policy com Principal "*" foi removida.
# Para compartilhar arquivos com quem está fora da empresa, usar URLs pré-assinadas.
