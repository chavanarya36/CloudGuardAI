resource "aws_s3_bucket" "complete_bucket" {
  bucket = "company-secure-bucket"
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "aws:kms"
        kms_master_key_id = var.kms_key_id
      }
    }
  }

  logging {
    target_bucket = var.log_bucket_id
    target_prefix = "secure-bucket-logs/"
  }

  lifecycle_rule {
    enabled = true
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }

  tags = {
    Name        = "secure-bucket"
    Environment = "production"
  }
}
