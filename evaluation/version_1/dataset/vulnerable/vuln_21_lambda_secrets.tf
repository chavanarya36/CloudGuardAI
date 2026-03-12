resource "aws_lambda_function" "processor" {
  filename         = "lambda.zip"
  function_name    = "data-processor"
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("lambda.zip")

  environment {
    variables = {
      DB_HOST     = "prod-db.example.com"
      DB_NAME     = "appdb"
      DB_USER     = "lambda_user"
      DB_PASSWORD = "LambdaDBPass_2024!prod"
      API_KEY     = "sk-live-51j3kFz9YvPqR8mNdXwT"
    }
  }

  tags = {
    Name        = "data-processor"
    Environment = "production"
  }
}
