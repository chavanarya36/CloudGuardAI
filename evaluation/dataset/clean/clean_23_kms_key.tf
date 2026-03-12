resource "aws_kms_key" "main" {
  description             = "Main encryption key for production workloads"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AdminKeyAccess"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${var.account_id}:role/admin" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "ServiceKeyUsage"
        Effect    = "Allow"
        Principal = { AWS = var.service_role_arn }
        Action    = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"]
        Resource  = "*"
      }
    ]
  })

  tags = {
    Name        = "main-kms-key"
    Environment = "production"
  }
}
