# Case Study: Realistic multi-tier web application infrastructure
# Patterns sourced from TerraGoat and real GitHub IaC repos

provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# --- VPC & Networking ---
resource "aws_security_group" "web_sg" {
  name        = "web-server-sg"
  description = "Allow inbound traffic to web servers"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # SSH open to world
  }

  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # RDP open to world
  }

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # All ports open
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]  # Unrestricted egress
  }
}

# --- EC2 Instance ---
resource "aws_instance" "web_server" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t2.micro"
  monitoring             = false  # No detailed monitoring
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    export DB_PASSWORD="SuperSecret123!"
    export API_KEY="sk-proj-abc123def456ghi789"
    apt-get update && apt-get install -y nginx
  EOF

  vpc_security_group_ids = [aws_security_group.web_sg.id]
}

# --- S3 Bucket ---
resource "aws_s3_bucket" "app_data" {
  bucket = "mycompany-app-data-prod"
  acl    = "public-read"  # Publicly readable

  versioning {
    enabled = false  # No versioning
  }
}

# --- RDS Database ---
resource "aws_db_instance" "main_db" {
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "webapp"
  username               = "admin"
  password               = "HardcodedPassword123!"  # Hardcoded password
  publicly_accessible    = true                      # Public DB
  storage_encrypted      = false                     # Unencrypted storage
  skip_final_snapshot    = true                       # Skip snapshot on delete
  backup_retention_period = 0
}

# --- IAM ---
resource "aws_iam_policy" "admin_policy" {
  name = "super-admin"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"           # Wildcard IAM policy
      Resource = "*"
    }]
  })
}

resource "aws_iam_user" "deploy_user" {
  name = "deploy-bot"
}

# --- EBS Volume ---
resource "aws_ebs_volume" "data_vol" {
  availability_zone = "us-east-1a"
  size              = 100
  encrypted         = false  # Unencrypted EBS
}

# --- Lambda with secrets in env ---
resource "aws_lambda_function" "processor" {
  function_name = "data-processor"
  runtime       = "python3.9"
  handler       = "lambda_function.handler"
  filename      = "processor.zip"
  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      DB_HOST     = aws_db_instance.main_db.address
      DB_PASSWORD = "LambdaDbPass456!"
      API_SECRET  = "super-secret-api-key-12345"
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda-processor-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}
