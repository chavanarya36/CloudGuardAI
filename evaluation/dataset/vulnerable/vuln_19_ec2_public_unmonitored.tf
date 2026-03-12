resource "aws_instance" "web_server" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.medium"
  associate_public_ip_address = true
  monitoring                  = false
  key_name                    = var.key_name

  vpc_security_group_ids = [var.sg_id]
  subnet_id              = var.public_subnet_id

  tags = {
    Name        = "web-server"
    Environment = "production"
  }
}
