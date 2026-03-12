resource "aws_db_instance" "analytics" {
  identifier           = "analytics-db"
  engine               = "postgres"
  engine_version       = "14.7"
  instance_class       = "db.r5.large"
  allocated_storage    = 500
  storage_encrypted    = true
  publicly_accessible  = false
  db_name              = "analytics"
  username             = var.db_username
  password             = var.db_password
  skip_final_snapshot  = false
  final_snapshot_identifier = "analytics-final-snapshot"

  vpc_security_group_ids = [var.db_sg_id]
  db_subnet_group_name   = var.db_subnet_group

  backup_retention_period = 14
  deletion_protection     = true

  tags = {
    Name        = "analytics-db"
    Environment = "production"
  }
}
