variable "region" {
  default = "us-east-1"
}

resource "aws_instance" "bastion" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  key_name      = "bastion-key"

  connection {
    type     = "ssh"
    user     = "ec2-user"
    password = "B@stionAccess2024!Secret"
    host     = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "echo 'Setup complete'"
    ]
  }

  tags = {
    Name = "bastion-host"
  }
}
