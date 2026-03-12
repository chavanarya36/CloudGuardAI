resource "aws_s3_bucket" "public_data" {
  bucket = "company-public-assets"
  acl    = "public-read"

  tags = {
    Name        = "public-assets"
    Environment = "production"
  }
}
