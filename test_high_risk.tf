############################################################
# High-Risk Terraform Test File for CloudGuard AI Interface
# Purpose: Exercise feature extractor & risk model
# Contains: Public S3 bucket, overly permissive security group,
#           inline secrets pattern, admin IAM policy attachment,
#           disabled encryption/logging, open ingress rules.
############################################################

terraform {
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = "us-east-1"
}

# 1. Public S3 bucket with ACL + public access block disabled
resource "aws_s3_bucket" "public_data" {
  bucket = "cgai-test-public-bucket-example"
  tags = {
    Environment = "dev"
    Owner       = "test"
  }
}

# Explicit (and risky) public ACL
resource "aws_s3_bucket_acl" "public_acl" {
  bucket = aws_s3_bucket.public_data.id
  acl    = "public-read"
}

# Public access block weakened
resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket                  = aws_s3_bucket.public_data.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# No server-side encryption block (omitted intentionally)

# 2. Security group allowing full ingress from anywhere
resource "aws_security_group" "open_sg" {
  name        = "open-ingress-sg"
  description = "Overly permissive SG for testing"
  vpc_id      = "vpc-12345678"

  ingress {
    description = "SSH open to world"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP open to world"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "All ports open (test pattern)"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All egress"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Purpose = "risk-demo"
  }
}

# 3. IAM user with admin policy attachment
resource "aws_iam_user" "priv_user" {
  name = "cgai-risk-admin-user"
  tags = {
    Role = "test-admin"
  }
}

resource "aws_iam_user_policy_attachment" "admin_attach" {
  user       = aws_iam_user.priv_user.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# 4. Hard-coded secret pattern (simulated; not real credentials)
# This is to trigger token/path feature sensitivity, DO NOT USE REAL SECRETS
locals {
  db_password = "SuperSecretPassword123!"
  api_key     = "AKIAFAKEKEYEXAMPLE1234"
}

# 5. Unencrypted EBS volume
resource "aws_ebs_volume" "unencrypted_vol" {
  availability_zone = "us-east-1a"
  size              = 10
  encrypted         = false
  tags = {
    Name = "unencrypted-test-volume"
  }
}

# 6. Open KMS-like pattern (simulated) - no actual key created
# (Deliberately omitted kms_key_id usage for encryption fields)

# 7. Output that may leak info
output "public_bucket_name" {
  value = aws_s3_bucket.public_data.bucket
}

output "open_sg_id" {
  value = aws_security_group.open_sg.id
}

# 8. Resource naming & tokens chosen to trigger path/resource token features:
#    - public, open, admin, unencrypted, secret, password, api_key
