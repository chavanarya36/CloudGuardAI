resource "aws_s3_bucket" "audit_logs" {
  bucket = "company-audit-logs"
  acl    = "private"

  versioning {
    enabled = false
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }

  tags = {
    Name = "audit-logs"
  }
}

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/app/production"
  retention_in_days = 7

  tags = {
    Environment = "production"
  }
}

resource "aws_flow_log" "vpc_flow" {
  vpc_id          = var.vpc_id
  traffic_type    = "ALL"
  log_destination = aws_cloudwatch_log_group.app_logs.arn
  iam_role_arn    = var.flow_log_role_arn

  tags = {
    Name            = "vpc-flow-log"
    enable_logging  = false
  }
}
