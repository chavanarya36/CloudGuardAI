resource "aws_s3_bucket" "encrypted_store" {
  bucket = "company-encrypted-store"
  acl    = "private"

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
    target_prefix = "encrypted-store-logs/"
  }

  tags = {
    Name        = "encrypted-store"
    Environment = "production"
  }
}
