resource "aws_s3_bucket" "public_bucket" {
  bucket = "my-public-bucket"
  acl    = "public-read"  # CRITICAL: Publicly accessible bucket
}

resource "aws_security_group" "wide_open" {
  name = "allow-all"
  
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # CRITICAL: Open to entire internet
  }
}

resource "aws_db_instance" "database" {
  identifier        = "mydb"
  engine            = "postgres"
  instance_class    = "db.t3.micro"
  username          = "admin"
  password          = "hardcoded-password-123"  # CRITICAL: Hardcoded password
  skip_final_snapshot = true
  publicly_accessible = true  # HIGH: Database exposed to internet
  storage_encrypted   = false  # MEDIUM: Encryption not enabled
}

resource "aws_iam_user_policy" "admin_access" {
  name = "admin-policy"
  user = aws_iam_user.developer.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"  # CRITICAL: Full admin access
      Resource = "*"
    }]
  })
}

resource "aws_instance" "web_server" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  
  metadata_options {
    http_tokens = "optional"  # MEDIUM: IMDSv2 not enforced
  }
  
  # No monitoring enabled
  # No encryption
}
