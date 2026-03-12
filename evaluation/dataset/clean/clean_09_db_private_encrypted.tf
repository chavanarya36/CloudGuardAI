resource "aws_db_instance" "main" {
  identifier           = "production-db"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  storage_encrypted    = true
  publicly_accessible  = false
  db_name              = "appdb"
  username             = "admin"
  password             = var.db_password
  skip_final_snapshot  = false
  final_snapshot_identifier = "prod-db-final-snapshot"

  vpc_security_group_ids = [var.db_sg_id]
  db_subnet_group_name   = var.db_subnet_group

  backup_retention_period = 7
  multi_az                = true

  tags = {
    Name        = "production-db"
    Environment = "production"
  }
}
