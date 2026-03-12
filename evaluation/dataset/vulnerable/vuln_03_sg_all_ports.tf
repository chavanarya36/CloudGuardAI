resource "aws_security_group" "permissive" {
  name        = "permissive-sg"
  description = "Overly permissive security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "All traffic"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "permissive-sg"
  }
}
