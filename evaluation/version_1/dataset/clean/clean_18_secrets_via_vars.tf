resource "aws_ssm_parameter" "api_secret" {
  name   = "/app/api-secret"
  type   = "SecureString"
  value  = var.api_secret_value
  key_id = var.kms_key_id
}

resource "aws_secretsmanager_secret" "db_creds" {
  name       = "production/db-credentials"
  kms_key_id = var.kms_key_id
}

resource "aws_secretsmanager_secret_version" "db_creds" {
  secret_id     = aws_secretsmanager_secret.db_creds.id
  secret_string = var.db_credentials_json
}
