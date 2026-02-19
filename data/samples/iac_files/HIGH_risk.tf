# Synthetic HIGH risk Terraform sample
# Intent: Trigger multiple high-severity findings (public S3, wide-open SG, hard-coded secret)

terraform {
  required_version = ">= 0.13"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Wide-open security group (0.0.0.0/0) on SSH and HTTP
resource "aws_security_group" "open_sg" {
  name        = "open-sg"
  description = "Open to the world"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Public S3 bucket with ACL and website hosting
resource "aws_s3_bucket" "public_bucket" {
  bucket = "synthetic-high-risk-bucket-example"
  acl    = "public-read"

  website {
    index_document = "index.html"
    error_document = "error.html"
  }
}

resource "aws_s3_bucket_public_access_block" "public_bucket_block" {
  bucket                  = aws_s3_bucket.public_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Hard-coded secret (anti-pattern for testing only)
variable "db_password" {
  default = "SuperSecret123!" # unsafe
}

output "insecure_secret_echo" {
  value = var.db_password
}
