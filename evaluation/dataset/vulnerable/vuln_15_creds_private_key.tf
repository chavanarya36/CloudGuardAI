resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."
}

resource "tls_private_key" "deploy_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Vulnerable: private key written to local file and referenced in config
resource "local_file" "private_key" {
  content  = <<-EOT
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyFHPmGBFnDLFGkR2jFGI7kcBU
Rz3JUmDoNiQ+WPTz8AjyoE3NOzfGBH3JGkUGRPZevOJMIXF41OEJbK2kq+kZ
wJalrXUtnFEMIK7MDENG/bPxRfiCYEXAMPLEKEYAbClRnkFT5VU2RdOBg9aLq
-----END RSA PRIVATE KEY-----
  EOT
  filename = "${path.module}/deploy_key.pem"
}
