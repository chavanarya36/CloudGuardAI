resource "aws_lambda_function" "processor" {
  filename         = "lambda.zip"
  function_name    = "data-processor"
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("lambda.zip")

  environment {
    variables = {
      DB_HOST          = var.db_host
      DB_NAME          = var.db_name
      SECRET_STORE_ARN = var.secret_arn
      LOG_LEVEL        = "INFO"
    }
  }

  tags = {
    Name        = "data-processor"
    Environment = "production"
  }
}
