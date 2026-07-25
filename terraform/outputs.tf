output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.aura.id
}

output "rds_endpoint" {
  description = "Amazon RDS PostgreSQL endpoint"
  value       = aws_db_instance.aura.endpoint
}

output "rds_database_url" {
  description = "Full database URL for services"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.aura.address}:5432/${var.db_name}"
  sensitive   = true
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API endpoint"
  value       = module.eks.cluster_endpoint
}

output "lambda_function_arn" {
  description = "AI Agent Lambda trigger ARN"
  value       = aws_lambda_function.rca_trigger.arn
}

output "sns_topic_arn" {
  description = "Escalation SNS topic ARN"
  value       = aws_sns_topic.escalation.arn
}

output "eventbridge_rule_arn" {
  description = "CloudWatch to Lambda EventBridge rule ARN"
  value       = aws_cloudwatch_event_rule.rca_trigger.arn
}

output "sqs_queue_url" {
  description = "Event-driven SQS queue URL"
  value       = aws_sqs_queue.event_queue.url
}
