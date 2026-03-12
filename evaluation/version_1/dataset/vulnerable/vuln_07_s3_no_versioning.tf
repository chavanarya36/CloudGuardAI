resource "aws_s3_bucket" "logs" {
  bucket = "company-application-logs"
  acl    = "private"

  versioning {
    enabled = false
  }

  tags = {
    Name        = "app-logs"
    Environment = "production"
  }
}
