resource "aws_s3_bucket" "sensitive_data" {
  bucket = "company-sensitive-records"
  acl    = "private"

  versioning {
    enabled = true
  }

  tags = {
    Name        = "sensitive-records"
    Environment = "production"
  }
}
