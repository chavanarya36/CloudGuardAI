resource "aws_security_group" "rdp_access" {
  name        = "rdp-access"
  description = "Allow RDP access"
  vpc_id      = var.vpc_id

  ingress {
    description = "RDP from anywhere"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rdp-access"
  }
}
