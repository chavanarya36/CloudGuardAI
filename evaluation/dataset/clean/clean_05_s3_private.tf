resource "aws_s3_bucket" "private_data" {
  bucket = "company-private-assets"
  acl    = "private"

  logging {
    target_bucket = var.log_bucket_id
    target_prefix = "s3-access-logs/"
  }

  tags = {
    Name        = "private-assets"
    Environment = "production"
  }
}
