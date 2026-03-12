resource "aws_s3_bucket" "upload_bucket" {
  bucket = "company-user-uploads"
  acl    = "public-read-write"

  tags = {
    Name        = "user-uploads"
    Environment = "staging"
  }
}
