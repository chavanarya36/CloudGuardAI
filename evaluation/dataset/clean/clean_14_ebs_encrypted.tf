resource "aws_ebs_volume" "data_volume" {
  availability_zone = "us-east-1a"
  size              = 100
  type              = "gp3"
  encrypted         = true
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "data-volume"
    Environment = "production"
  }
}

resource "aws_volume_attachment" "data_attach" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.data_volume.id
  instance_id = var.instance_id
}
