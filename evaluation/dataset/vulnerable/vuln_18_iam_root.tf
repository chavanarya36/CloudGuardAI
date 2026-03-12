resource "aws_iam_policy" "cross_account" {
  name = "cross-account-root-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "arn:aws:s3:::shared-bucket/*"
        Principal = {
          AWS = "arn:aws:iam::123456789012:root"
        }
      }
    ]
  })
}
