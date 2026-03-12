resource "aws_security_group" "db_sg" {
  name        = "database-sg"
  description = "Database security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "MySQL from app tier"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  tags = {
    Name = "database-sg"
  }
}

resource "aws_db_instance" "database" {
  identifier           = "secure-database"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  publicly_accessible  = false
  storage_encrypted    = true
  db_name              = "appdb"
  username             = var.db_username
  password             = var.db_password
  skip_final_snapshot  = false
  final_snapshot_identifier = "secure-db-final"

  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = var.db_subnet_group

  tags = {
    Name        = "secure-database"
    Environment = "production"
  }
}
