#!/bin/bash

# --- CONFIGURATION ---
# This automatically gets your 12-digit AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
REPO_NAME="my-devops-mentor"
LAMBDA_NAME="DevOpsMentorBot"

echo "🚀 Starting Deployment for $REPO_NAME..."

# 1. Login to Amazon ECR
# This gives Docker permission to talk to your AWS "shelf"
echo "🔑 Logging into Amazon ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# 2. Build the Docker Image
# The --platform flag ensures it works on AWS even if you use a Mac M1/M2/M3
echo "📦 Building Docker image..."
docker build --platform linux/amd64 -t $REPO_NAME .

# 3. Tag the Image
# This tells Docker exactly which AWS folder to target
echo "🏷️ Tagging image..."
docker tag $REPO_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# 4. Push to ECR
# This uploads your code to the cloud
echo "📤 Pushing image to AWS ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# 5. Force Lambda to update
# NOTE: This will fail on the VERY FIRST run because the Lambda doesn't exist yet. 
# That is expected! Once you run 'terraform apply' the first time, this will work forever.
echo "🔄 Attempting to update Lambda function code..."
aws lambda update-function-code --function-name $LAMBDA_NAME --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest || echo "⚠️ Lambda not found yet. This is normal for the first run!"

echo "✅ Script Finished!"