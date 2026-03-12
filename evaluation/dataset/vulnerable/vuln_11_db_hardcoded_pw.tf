resource "aws_db_instance" "backend" {
  identifier           = "backend-db"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.medium"
  allocated_storage    = 50
  storage_encrypted    = true
  publicly_accessible  = false
  db_name              = "backend"
  username             = "dbadmin"
  password             = "SuperSecret123!"
  skip_final_snapshot  = false

  vpc_security_group_ids = [var.db_sg_id]
  db_subnet_group_name   = var.db_subnet_group

  tags = {
    Name        = "backend-db"
    Environment = "production"
  }
}
