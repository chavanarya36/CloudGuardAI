# =============================================================================
# TerraGoat Case Study: Insecure Lambda + API Gateway Pipeline
# Source: Patterns from BridgeCrew/TerraGoat and serverless breach patterns
# Scenario: A FinTech startup deploys a payment processing pipeline using
#           Lambda functions with hardcoded secrets, over-privileged IAM,
#           and unencrypted data at rest
# =============================================================================

provider "aws" {
  region = "us-east-1"
}

# --- Lambda: Payment Processor ---
resource "aws_lambda_function" "payment_processor" {
  function_name = "payment-processor-prod"
  runtime       = "python3.11"
  handler       = "handler.process_payment"
  filename      = "payment_processor.zip"
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 30
  memory_size   = 256

  environment {
    variables = {
      STRIPE_SECRET_KEY    = "sk_live_51ABC123DEF456GHI789JKL"   # VULN: Hardcoded Stripe key
      DB_PASSWORD          = "PaymentDB!Prod#2024"                # VULN: Hardcoded DB password
      ENCRYPTION_KEY       = "aes-256-cbc-key-do-not-commit"      # VULN: Hardcoded encryption key
      JWT_SIGNING_SECRET   = "jwt-hmac-secret-production-key"     # VULN: Hardcoded JWT secret
      PLAID_CLIENT_SECRET  = "plaid_secret_prod_abc123def456"     # VULN: Hardcoded Plaid secret
      LOG_LEVEL            = "DEBUG"                               # VULN: Debug logging in prod
    }
  }

  # No VPC config - runs in default Lambda network   # VULN: Not in VPC
  # No reserved concurrency                          # VULN: No throttling protection
  # No dead letter queue                             # VULN: Failed events lost
}

# --- Lambda: User Auth ---
resource "aws_lambda_function" "user_auth" {
  function_name = "user-auth-prod"
  runtime       = "nodejs18.x"
  handler       = "auth.handler"
  filename      = "user_auth.zip"
  role          = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      COGNITO_CLIENT_SECRET = "cognito-secret-abc123xyz789"       # VULN: Hardcoded secret
      REDIS_PASSWORD        = "redis!Prod2024#Cache"               # VULN: Hardcoded password
      API_KEY               = "api-key-production-12345-abcdef"    # VULN: Hardcoded API key
    }
  }
}

# --- IAM Role for Lambda (over-privileged) ---
resource "aws_iam_role" "lambda_exec" {
  name = "payment-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda-full-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"                     # VULN: Wildcard - full AWS admin
        Resource = "*"
      }
    ]
  })
}

# --- DynamoDB (no encryption, no PITR) ---
resource "aws_dynamodb_table" "transactions" {
  name           = "payment-transactions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  # No server_side_encryption    # VULN: Unencrypted table (has PII/payment data)
  # No point_in_time_recovery    # VULN: No PITR backup
  # No stream_enabled            # VULN: No audit trail

  tags = {
    Environment = "production"
    Compliance  = "pci-dss"      # Ironic: claims PCI-DSS but violates it
  }
}

# --- S3 Bucket for payment receipts ---
resource "aws_s3_bucket" "payment_receipts" {
  bucket = "fintech-payment-receipts-prod"
  acl    = "public-read"           # VULN: Payment receipts publicly readable!

  versioning {
    enabled = false                # VULN: No versioning on financial data
  }
}

# --- SNS Topic (unencrypted) ---
resource "aws_sns_topic" "payment_notifications" {
  name = "payment-events-prod"
  # No kms_master_key_id       # VULN: SNS topic not encrypted
}

# --- CloudWatch (minimal retention) ---
resource "aws_cloudwatch_log_group" "payment_logs" {
  name              = "/lambda/payment-processor"
  retention_in_days = 3              # VULN: Only 3 days retention for financial logs
  # No KMS encryption              # VULN: Logs contain sensitive payment data
}

# --- Security Group for VPC Lambda (if used) ---
resource "aws_security_group" "lambda_sg" {
  name        = "lambda-payment-sg"
  description = "Lambda payment processor SG"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]     # VULN: All ports open
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]     # VULN: Unrestricted egress
  }
}

# --- RDS for transaction history ---
resource "aws_db_instance" "payment_db" {
  identifier          = "payment-history-db"
  engine              = "mysql"
  engine_version      = "8.0"
  instance_class      = "db.r5.large"
  allocated_storage   = 200
  db_name             = "payments"
  username            = "payment_admin"
  password            = "FinTech#DB!Prod2024"        # VULN: Hardcoded password
  publicly_accessible = true                          # VULN: Public database
  storage_encrypted   = false                         # VULN: Unencrypted storage
  skip_final_snapshot = true                           # VULN: No final snapshot
  backup_retention_period = 1                          # VULN: Only 1 day backup for financial data
}
