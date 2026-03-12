resource "aws_s3_bucket" "data_lake" {
  bucket = "company-data-lake"
  acl    = "public-read"

  versioning {
    enabled = false
  }

  tags = {
    Name        = "data-lake"
    Environment = "production"
  }
}
