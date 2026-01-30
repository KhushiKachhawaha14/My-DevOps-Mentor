# 1. Define the AWS Provider
provider "aws" {
  region = "us-east-1" 
}

# --- ECR SECTION (The Storage) ---

resource "aws_ecr_repository" "mentor_bot" {
  name                 = "my-devops-mentor"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Allows terraform destroy to work easily

  image_scanning_configuration {
    scan_on_push = true 
  }
}

resource "aws_ecr_lifecycle_policy" "cleanup" {
  repository = aws_ecr_repository.mentor_bot.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1,
      description  = "Keep only the 2 most recent images to save space/cost",
      selection = {
        tagStatus     = "any",
        countType     = "imageCountMoreThan",
        countNumber   = 2
      },
      action = { type = "expire" }
    }]
  })
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

# Attach basic execution policy (allows logging to CloudWatch)
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- LAMBDA SECTION (The Bot) ---

resource "aws_lambda_function" "bot_lambda" {
  function_name = "DevOpsMentorBot"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.mentor_bot.repository_url}:latest"
  timeout       = 60 # Important: Gives Gemini time to think

  # Add your environment variables here
  environment {
    variables = {
      GEMINI_API_KEY = "PLACEHOLDER" # Use variables in production
      GMAIL_USER     = "PLACEHOLDER"
    }
  }
}

# --- API GATEWAY SECTION (The Front Door) ---

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

# Permission for API Gateway to call Lambda
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