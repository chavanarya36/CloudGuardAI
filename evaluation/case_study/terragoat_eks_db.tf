# =============================================================================
# TerraGoat Case Study: Insecure EKS Cluster with Exposed Database
# Source: Patterns from BridgeCrew/TerraGoat and real breach post-mortems
# Scenario: DevOps team deploys an EKS-backed microservice platform with
#           publicly accessible RDS, overly permissive security groups,
#           missing encryption, and hardcoded credentials
# =============================================================================

provider "aws" {
  region = "eu-west-1"
}

# --- VPC Networking ---
resource "aws_security_group" "eks_cluster_sg" {
  name        = "eks-cluster-sg"
  description = "EKS cluster security group"
  vpc_id      = "vpc-0abc123def456"

  # VULN: SSH open to the entire internet
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # VULN: Kubernetes API open to the internet
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Kubernetes API"
  }

  # VULN: NodePort range wide open
  ingress {
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "NodePort services"
  }

  # VULN: All egress open
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "eks-cluster-sg"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "rds-database-sg"
  description = "RDS database security group"
  vpc_id      = "vpc-0abc123def456"

  # VULN: Database port open to entire internet
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "PostgreSQL"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- RDS Database ---
resource "aws_db_instance" "platform_db" {
  identifier             = "platform-primary-db"
  engine                 = "postgres"
  engine_version         = "14.7"
  instance_class         = "db.r5.large"
  allocated_storage      = 100
  max_allocated_storage  = 500
  db_name                = "platform"
  username               = "dbadmin"
  password               = "Pr0duction!DB#2024Secure"   # VULN: Hardcoded password
  publicly_accessible    = true                          # VULN: Public database
  storage_encrypted      = false                         # VULN: Unencrypted storage
  skip_final_snapshot    = true                           # VULN: No final snapshot
  backup_retention_period = 0                             # VULN: No backups
  multi_az               = false                          # VULN: No multi-AZ
  deletion_protection    = false                          # VULN: No deletion protection

  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  tags = {
    Environment = "production"
    Service     = "platform-api"
  }
}

# --- EC2 Bastion Host ---
resource "aws_instance" "bastion" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.medium"
  associate_public_ip_address = true
  monitoring                  = false   # VULN: No detailed monitoring

  user_data = <<-EOF
    #!/bin/bash
    export DATABASE_URL="postgresql://dbadmin:Pr0duction!DB#2024Secure@platform-primary-db.cluster-abc123.eu-west-1.rds.amazonaws.com:5432/platform"
    export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
    export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    export JWT_SECRET="my-super-secret-jwt-key-do-not-share"
    curl -sfL https://get.k8s.io | bash -
  EOF

  vpc_security_group_ids = [aws_security_group.eks_cluster_sg.id]

  tags = {
    Name = "eks-bastion"
  }
}

# --- EBS Volumes ---
resource "aws_ebs_volume" "db_data" {
  availability_zone = "eu-west-1a"
  size              = 500
  encrypted         = false    # VULN: Unencrypted EBS volume
  type              = "gp3"

  tags = {
    Name = "db-data-volume"
  }
}

# --- IAM Roles ---
resource "aws_iam_policy" "eks_admin_policy" {
  name = "eks-cluster-admin"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"            # VULN: Full admin wildcard
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user" "ci_cd_user" {
  name = "ci-cd-deployer"
}

resource "aws_iam_access_key" "ci_cd_key" {
  user = aws_iam_user.ci_cd_user.name
  # VULN: Long-lived IAM access keys for CI/CD (should use OIDC/roles)
}

# --- CloudWatch Logging (disabled) ---
resource "aws_cloudwatch_log_group" "eks_logs" {
  name              = "/eks/platform-cluster"
  retention_in_days = 1          # VULN: Minimal log retention (1 day)
}
