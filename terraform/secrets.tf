resource "aws_secretsmanager_secret" "db_password" {
  name        = "aura-commerce/db-password"
  description = "PostgreSQL master password for AuraCommerce RDS"
  tags = {
    Project = "AuraCommerce"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

resource "aws_secretsmanager_secret" "auth_secret_key" {
  name        = "aura-commerce/auth-secret"
  description = "JWT secret key for Auth Service"
  tags = {
    Project = "AuraCommerce"
  }
}

resource "aws_secretsmanager_secret_version" "auth_secret_key" {
  secret_id     = aws_secretsmanager_secret.auth_secret_key.id
  secret_string = "aura-commerce-secret-2026"
}

resource "aws_secretsmanager_secret" "event_queue_url" {
  name        = "aura-commerce/sqs-queue-url"
  description = "SQS event queue URL for event-driven services"
  tags = {
    Project = "AuraCommerce"
  }
}

resource "aws_secretsmanager_secret_version" "event_queue_url" {
  secret_id     = aws_secretsmanager_secret.event_queue_url.id
  secret_string = aws_sqs_queue.event_queue.url
}
