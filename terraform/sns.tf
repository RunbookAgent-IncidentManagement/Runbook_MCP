resource "aws_sns_topic" "escalation" {
  name = "escalation-topic"

  tags = {
    Name        = "AuraCommerce Escalation"
    Project     = "AuraCommerce"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = aws_sns_topic.escalation.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.rca_trigger.arn
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.escalation.arn
  protocol  = "email"
  endpoint  = "sre-oncall@aura-commerce.local"
}
