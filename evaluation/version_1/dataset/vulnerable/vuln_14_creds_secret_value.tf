resource "aws_ssm_parameter" "api_secret" {
  name  = "/app/api-secret"
  type  = "String"
  value = "sk-proj-abc123def456ghi789jkl012mno345pqr678"
}

resource "aws_secretsmanager_secret" "db_creds" {
  name = "production/db-credentials"
}

resource "aws_secretsmanager_secret_version" "db_creds" {
  secret_id     = aws_secretsmanager_secret.db_creds.id
  secret_string = jsonencode({
    username = "admin"
    password = "Pr0duction_P@ssw0rd_2024!"
  })
}
