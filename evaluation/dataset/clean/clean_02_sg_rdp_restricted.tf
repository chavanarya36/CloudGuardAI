resource "aws_security_group" "rdp_access" {
  name        = "rdp-access"
  description = "Allow RDP from management subnet"
  vpc_id      = var.vpc_id

  ingress {
    description = "RDP from management network"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["172.16.0.0/16"]
  }

  tags = {
    Name = "rdp-access"
  }
}
