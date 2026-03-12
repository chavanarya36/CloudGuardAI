resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Web tier security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from ALB"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    description = "Database access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.10.0.0/16"]
  }
}

resource "aws_instance" "web_server" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.large"
  associate_public_ip_address = false
  monitoring                  = true
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  subnet_id                   = var.private_subnet_id

  tags = {
    Name = "web-server"
  }
}

resource "aws_s3_bucket" "app_data" {
  bucket = "webapp-data-store"
  acl    = "private"

  logging {
    target_bucket = var.log_bucket_id
    target_prefix = "app-data-logs/"
  }

  tags = {
    Name = "app-data"
  }
}

resource "aws_db_instance" "backend_db" {
  identifier          = "backend-db"
  engine              = "postgres"
  instance_class      = "db.r5.large"
  allocated_storage   = 200
  publicly_accessible = false
  storage_encrypted   = true
  db_name             = "webapp"
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = false
  final_snapshot_identifier = "backend-db-final-snapshot"

  vpc_security_group_ids = [var.db_sg_id]

  tags = {
    Name = "backend-db"
  }
}

resource "aws_iam_role" "app_role" {
  name = "webapp-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "app_policy" {
  name = "webapp-policy"
  role = aws_iam_role.app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "logs:PutLogEvents"]
      Resource = ["arn:aws:s3:::webapp-data-store/*", "arn:aws:logs:*:*:*"]
    }]
  })
}
