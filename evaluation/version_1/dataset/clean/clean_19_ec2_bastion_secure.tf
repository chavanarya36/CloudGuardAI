resource "aws_instance" "bastion" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.micro"
  associate_public_ip_address = false
  monitoring                  = true
  key_name                    = var.key_name

  vpc_security_group_ids = [var.bastion_sg_id]
  subnet_id              = var.private_subnet_id

  tags = {
    Name        = "bastion-host"
    Environment = "production"
  }
}
