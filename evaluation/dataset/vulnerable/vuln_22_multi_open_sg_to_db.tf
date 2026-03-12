resource "aws_security_group" "db_sg" {
  name        = "database-sg"
  description = "Database security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "MySQL from anywhere"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "database-sg"
  }
}

resource "aws_db_instance" "database" {
  identifier           = "exposed-database"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  publicly_accessible  = true
  storage_encrypted    = false
  db_name              = "appdb"
  username             = "admin"
  password             = "DatabaseP@ss123"
  skip_final_snapshot  = true

  vpc_security_group_ids = [aws_security_group.db_sg.id]

  tags = {
    Name        = "exposed-database"
    Environment = "production"
  }
}
