resource "aws_s3_bucket" "backup" {
  bucket = "company-backup-store"
  acl    = "private"

  versioning {
    enabled = false
  }

  logging {
    target_bucket = var.log_bucket_id
    target_prefix = "backup-logs/"
  }

  tags = {
    Name        = "backup-store"
    Environment = "production"
  }
}
