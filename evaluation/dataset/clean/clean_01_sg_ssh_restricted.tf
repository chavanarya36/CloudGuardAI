resource "aws_security_group" "ssh_access" {
  name        = "ssh-access"
  description = "Allow SSH from VPN only"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH from corporate VPN"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  tags = {
    Name        = "ssh-access"
    Environment = "production"
  }
}
