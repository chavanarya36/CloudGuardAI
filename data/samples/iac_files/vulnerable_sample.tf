resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "my-vulnerable-bucket"
  acl    = "public-read"  # Security issue: public ACL

  versioning {
    enabled = false  # Security issue: versioning disabled
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Environment = "test"
    Purpose     = "scanner-demo"
  }
}

resource "aws_security_group" "wide_open" {
  name        = "wide-open-sg"
  description = "Insecure security group for testing"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Security issue: open to world
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "insecure_db" {
  allocated_storage    = 20
  engine               = "mysql"
  engine_version       = "5.7"
  instance_class       = "db.t2.micro"
  name                 = "testdb"
  username             = "admin"
  password             = "password123"  # Security issue: hardcoded password
  skip_final_snapshot  = true
  publicly_accessible  = true  # Security issue: publicly accessible
  storage_encrypted    = false  # Security issue: unencrypted storage

  tags = {
    Name = "test-database"
  }
}
