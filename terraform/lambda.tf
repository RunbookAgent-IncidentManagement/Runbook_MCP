resource "aws_iam_role" "lambda_rca" {
  name = "aura-lambda-rca-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "aura-lambda-rca-role"
  }
}

resource "aws_iam_policy" "lambda_rca_policy" {
  name        = "aura-lambda-rca-policy"
  description = "Permissions for Lambda AI Agent trigger"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:GetTopicAttributes"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "aura-lambda-rca-policy"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_rca_attach" {
  role       = aws_iam_role.lambda_rca.name
  policy_arn = aws_iam_policy.lambda_rca_policy.arn
}

resource "aws_lambda_function" "rca_trigger" {
  function_name = "aura-rca-trigger"
  role          = aws_iam_role.lambda_rca.arn
  handler       = "lambda_rca_trigger.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 256

  s3_bucket = var.lambda_s3_bucket
  s3_key    = "lambda/rca_trigger.zip"

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      RCA_AGENT_URL     = "http://rca-agent-service:8000/analyze"
      RUNBOOK_AGENT_URL = "http://runbook-agent-service:8001/execute"
      SNS_TOPIC_ARN     = aws_sns_topic.escalation.arn
      LOG_LEVEL         = "INFO"
    }
  }

  tags = {
    Name = "aura-rca-trigger"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_rca_attach
  ]
}
