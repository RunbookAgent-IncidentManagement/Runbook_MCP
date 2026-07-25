resource "aws_cloudwatch_event_rule" "rca_trigger" {
  name        = "CloudWatchAlarmToRCA"
  description = "Trigger Lambda when CloudWatch Alarm enters ALARM state"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = {
        value = ["ALARM"]
      }
    }
  })

  tags = {
    Name    = "CloudWatchAlarmToRCA"
    Project = "AuraCommerce"
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.rca_trigger.name
  target_id = "RCA_Lambda_Target"
  arn       = aws_lambda_function.rca_trigger.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rca_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rca_trigger.arn
}
