resource "aws_security_group" "app_egress" {
  name        = "app-egress"
  description = "Restricted egress for application tier"
  vpc_id      = var.vpc_id

  egress {
    description = "HTTPS to AWS services"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    description = "Database access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.10.0.0/16"]
  }

  tags = {
    Name = "app-egress"
  }
}
