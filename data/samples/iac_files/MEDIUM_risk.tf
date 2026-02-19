# Synthetic MEDIUM risk Terraform sample
# Intent: Some risky defaults (unencrypted EBS, permissive SG on HTTP) but not fully critical

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

# Security group open for HTTP only, not SSH
resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "HTTP open to world"

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

# EBS volume missing encryption (depends on org policy)
resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 10
  type              = "gp2"
  # encryption not specified -> often flagged as medium
}
