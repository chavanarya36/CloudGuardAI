resource "aws_db_instance" "temp" {
  identifier           = "temp-reporting-db"
  engine               = "postgres"
  engine_version       = "14.7"
  instance_class       = "db.t3.small"
  allocated_storage    = 20
  storage_encrypted    = true
  publicly_accessible  = false
  db_name              = "reporting"
  username             = "reporter"
  password             = var.db_password
  skip_final_snapshot  = true

  vpc_security_group_ids = [var.db_sg_id]
  db_subnet_group_name   = var.db_subnet_group

  tags = {
    Name        = "temp-reporting-db"
    Environment = "staging"
  }
}
