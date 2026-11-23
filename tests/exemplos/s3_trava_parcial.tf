resource "aws_s3_bucket" "exemplo" {
  bucket = "acme-exemplo"
}

resource "aws_s3_bucket_public_access_block" "exemplo" {
  bucket = aws_s3_bucket.exemplo.id

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = true
}
