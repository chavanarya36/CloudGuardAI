resource "aws_security_group" "egress_all" {
  name        = "egress-all"
  description = "Security group with unrestricted egress"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "egress-all"
  }
}
