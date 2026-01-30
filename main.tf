# 1. Define the AWS Provider
provider "aws" {
  region = "us-east-1" 
}

# --- ECR SECTION (The Storage) ---
resource "aws_ecr_repository" "mentor_bot" {
  name                 = "my-devops-mentor"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true 
  }
}

# --- IAM SECTION (The Permissions) ---
resource "aws_iam_role" "lambda_exec" {
  name = "devops_mentor_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allows the bot to read your API keys from SSM
resource "aws_iam_policy" "lambda_ssm_policy" {
  name = "DevOpsMentorSSMRead"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "ssm:GetParameter"
      Effect   = "Allow"
      # IMPORTANT: Ensure your SSM parameters start with /mentor/
      Resource = "arn:aws:ssm:us-east-1:982068586284:parameter/mentor/*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_ssm_policy.arn
}

# --- LAMBDA SECTION (The Bot) ---
resource "aws_lambda_function" "bot_lambda" {
  function_name = "DevOpsMentorBot"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.mentor_bot.repository_url}:latest"
  timeout       = 60 

  environment {
    variables = {
      WEBHOOK_SECRET = var.webhook_secret
      GMAIL_USER     = var.gmail_user
    }
  }
}
# --- API GATEWAY SECTION ---
resource "aws_apigatewayv2_api" "bot_api" {
  name          = "DevOps-Mentor-Gateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "bot_stage" {
  api_id      = aws_apigatewayv2_api.bot_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda_link" {
  api_id           = aws_apigatewayv2_api.bot_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.bot_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "webhook_route" {
  api_id    = aws_apigatewayv2_api.bot_api.id
  route_key = "POST /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_link.id}"
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bot_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bot_api.execution_arn}/*/*"
}

# --- OUTPUTS ---
output "github_webhook_url" {
  value = aws_apigatewayv2_api.bot_api.api_endpoint
}