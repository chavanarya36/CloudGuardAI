resource "aws_rds_cluster" "aurora" {
  cluster_identifier      = "production-aurora"
  engine                  = "aurora-mysql"
  engine_version          = "5.7.mysql_aurora.2.11.2"
  master_username         = var.db_username
  master_password         = var.db_password
  storage_encrypted       = true
  kms_key_id              = var.kms_key_id
  backup_retention_period = 7
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "aurora-final-snapshot"

  vpc_security_group_ids = [var.db_sg_id]
  db_subnet_group_name   = var.db_subnet_group

  tags = {
    Name        = "production-aurora"
    Environment = "production"
  }
}
