resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Web tier security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 65535
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

resource "aws_instance" "web_server" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.large"
  associate_public_ip_address = true
  monitoring                  = false
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  subnet_id                   = var.public_subnet_id

  user_data = <<-EOF
    #!/bin/bash
    export DB_PASSWORD="MyWebAppDBSecret123"
    export API_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    /opt/app/start.sh
  EOF

  tags = {
    Name = "web-server"
  }
}

resource "aws_s3_bucket" "app_data" {
  bucket = "webapp-data-store"
  acl    = "public-read"

  tags = {
    Name = "app-data"
  }
}

resource "aws_db_instance" "backend_db" {
  identifier          = "backend-db"
  engine              = "postgres"
  instance_class      = "db.r5.large"
  allocated_storage   = 200
  publicly_accessible = true
  storage_encrypted   = false
  db_name             = "webapp"
  username            = "dbadmin"
  password            = "Pr0dDBP@ssw0rd!"
  skip_final_snapshot = true

  vpc_security_group_ids = [aws_security_group.web_sg.id]

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
      Action   = "*"
      Resource = "*"
    }]
  })
}
