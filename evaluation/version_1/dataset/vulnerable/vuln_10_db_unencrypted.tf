resource "aws_db_instance" "analytics" {
  identifier           = "analytics-db"
  engine               = "postgres"
  engine_version       = "14.7"
  instance_class       = "db.r5.large"
  allocated_storage    = 500
  storage_encrypted    = false
  publicly_accessible  = false
  db_name              = "analytics"
  username             = "analytics_admin"
  password             = var.db_password
  skip_final_snapshot  = false

  vpc_security_group_ids = [var.db_sg_id]
  db_subnet_group_name   = var.db_subnet_group

  tags = {
    Name        = "analytics-db"
    Environment = "production"
  }
}
