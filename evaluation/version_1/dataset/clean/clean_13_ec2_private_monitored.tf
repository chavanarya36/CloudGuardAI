resource "aws_instance" "app_server" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.medium"
  associate_public_ip_address = false
  monitoring                  = true
  key_name                    = var.key_name

  vpc_security_group_ids = [var.sg_id]
  subnet_id              = var.private_subnet_id

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name        = "app-server"
    Environment = "production"
  }
}
