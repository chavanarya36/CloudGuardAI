resource "aws_s3_bucket" "versioned_data" {
  bucket = "company-versioned-data"
  acl    = "private"

  versioning {
    enabled = true
  }

  logging {
    target_bucket = var.log_bucket_id
    target_prefix = "versioned-data-logs/"
  }

  tags = {
    Name        = "versioned-data"
    Environment = "production"
  }
}
