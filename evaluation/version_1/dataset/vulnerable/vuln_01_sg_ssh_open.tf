resource "aws_security_group" "ssh_access" {
  name        = "ssh-access"
  description = "Allow SSH access"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ssh-access"
    Environment = "production"
  }
}
