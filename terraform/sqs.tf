resource "aws_sqs_queue" "event_queue" {
  name                      = "aura-commerce-events"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 1209600
  receive_wait_time_seconds   = 20

  tags = {
    Name    = "AuraCommerce Events"
    Project = "AuraCommerce"
  }
}

resource "aws_sqs_queue" "event_dlq" {
  name = "aura-commerce-events-dlq"

  tags = {
    Name    = "AuraCommerce Events DLQ"
    Project = "AuraCommerce"
  }
}
