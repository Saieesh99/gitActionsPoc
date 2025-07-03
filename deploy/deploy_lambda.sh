#!/bin/bash

# Usage: bash deploy_lambda.sh <env>
# Example: bash deploy_lambda.sh dev

set -e  # Stop on any error

ENV=$1
FUNC_NAME="connect-lex-lambda"
ZIP_FILE="lambda_${ENV}.zip"
HANDLER="handler.lambda_handler"
RUNTIME="python3.12"
ROLE_ARN="arn:aws:iam::543032853012:role/my-lambda-exec-role"  # ❗Replace this

REGION=${AWS_REGION:-"us-east-1"}  # Uses env var or fallback

if [[ -z "$ENV" ]]; then
  echo "❌ ENV not provided. Usage: bash deploy_lambda.sh dev"
  exit 1
fi

echo "🔧 Preparing Lambda deployment for environment: $ENV"
cd lambda || { echo "❌ Missing lambda/ folder"; exit 1; }

# Zip the Lambda code
echo "📦 Creating deployment package: $ZIP_FILE"
zip -r9 "../$ZIP_FILE" . > /dev/null
cd ..

# Check if function exists
echo "🔍 Checking if Lambda function '$FUNC_NAME' exists..."
if aws lambda get-function --function-name "$FUNC_NAME" --region "$REGION" > /dev/null 2>&1; then
  echo "✅ Function exists. Updating code..."
  VERSION=$(aws lambda update-function-code \
    --function-name "$FUNC_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
    --region "$REGION" \
    --publish \
    --query 'Version' --output text)
else
  echo "🚧 Function not found. Creating new Lambda function..."
  VERSION=$(aws lambda create-function \
    --function-name "$FUNC_NAME" \
    --runtime "$RUNTIME" \
    --role "$ROLE_ARN" \
    --handler "$HANDLER" \
    --zip-file "fileb://$ZIP_FILE" \
    --region "$REGION" \
    --query 'Version' --output text)
fi

echo "✅ Lambda deployed and published version: $VERSION"

# Check if alias exists
echo "🔁 Checking for alias '$ENV'..."
ALIAS_EXISTS=$(aws lambda get-alias \
  --function-name "$FUNC_NAME" \
  --name "$ENV" \
  --region "$REGION" \
  --query 'Name' \
  --output text 2>/dev/null || echo "None")

if [[ "$ALIAS_EXISTS" == "$ENV" ]]; then
  echo "🔄 Updating alias '$ENV' to version $VERSION..."
  aws lambda update-alias \
    --function-name "$FUNC_NAME" \
    --name "$ENV" \
    --function-version "$VERSION" \
    --region "$REGION"
else
  echo "➕ Creating alias '$ENV' for version $VERSION..."
  aws lambda create-alias \
    --function-name "$FUNC_NAME" \
    --name "$ENV" \
    --function-version "$VERSION" \
    --region "$REGION"
fi

echo "🚀 Deployment complete! Alias '$ENV' now points to version $VERSION"
