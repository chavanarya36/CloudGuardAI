# =============================================================================
# TerraGoat Case Study: Insecure S3 Data Lake
# Source: Patterns from BridgeCrew/TerraGoat intentionally vulnerable repo
# Scenario: A data engineering team deploys an analytics data lake with
#           multiple S3 buckets lacking encryption, versioning, and access controls
# =============================================================================

provider "aws" {
  region     = "us-west-2"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# --- Raw data ingestion bucket ---
resource "aws_s3_bucket" "data_lake_raw" {
  bucket = "acme-data-lake-raw-prod"
  acl    = "public-read-write"       # VULN: Public read-write

  versioning {
    enabled = false                  # VULN: No versioning
  }

  tags = {
    Environment = "production"
    Team        = "data-engineering"
  }
}

# --- Processed data bucket ---
resource "aws_s3_bucket" "data_lake_processed" {
  bucket = "acme-data-lake-processed"
  acl    = "public-read"             # VULN: Public read

  versioning {
    enabled = false                  # VULN: No versioning
  }
}

# --- ML model artifacts bucket ---
resource "aws_s3_bucket" "ml_artifacts" {
  bucket = "acme-ml-models-prod"
  acl    = "private"

  # No server_side_encryption_configuration  # VULN: No encryption
  # No logging                               # VULN: No access logging
  # No versioning block                      # VULN: No versioning
}

# --- Static website hosting (misconfigured) ---
resource "aws_s3_bucket" "website" {
  bucket = "acme-public-site"
  acl    = "public-read"             # VULN: overly open for a content bucket

  website {
    index_document = "index.html"
    error_document = "error.html"
  }

  cors_rule {
    allowed_headers = ["*"]          # VULN: Wildcard CORS
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"]          # VULN: Any origin
    max_age_seconds = 3600
  }
}

# --- Backup bucket with lifecycle but no encryption ---
resource "aws_s3_bucket" "backups" {
  bucket = "acme-db-backups-prod"
  acl    = "private"

  lifecycle_rule {
    enabled = true
    transition {
      days          = 30
      storage_class = "GLACIER"
    }
    expiration {
      days = 365
    }
  }

  # No encryption                     # VULN: Backup data unencrypted
  # No versioning                     # VULN: Deleted backups unrecoverable
}

# --- IAM policy that grants overly broad S3 access ---
resource "aws_iam_policy" "data_engineer_policy" {
  name = "data-engineer-full-access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:*"            # VULN: Wildcard S3 actions
        Resource = "*"               # VULN: All resources
      },
      {
        Effect   = "Allow"
        Action   = "*"               # VULN: Full admin wildcard
        Resource = "*"
      }
    ]
  })
}
