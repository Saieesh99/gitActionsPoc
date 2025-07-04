#!/bin/bash

# Usage: bash deploy_lambda.sh <env>
# Example: bash deploy_lambda.sh dev

set -e  # Stop on any error

ENV=$1
FUNC_NAME="connect-lex-lambda"
ZIP_FILE="lambda_${ENV}.zip"
HANDLER="handler.lambda_handler"
RUNTIME="python3.12"
REGION=${AWS_REGION:-"us-east-1"}

# Fetch role ARN dynamically (assumes Terraform outputs it)
ROLE_ARN=$(terraform -chdir=terraform output -raw lambda_exec_role_arn 2>/dev/null || echo "")

# Fallback role ARN (you can delete this once Terraform output works)
if [[ -z "$ROLE_ARN" ]]; then
  echo "⚠️ Terraform output not found. Falling back to hardcoded ARN"
  ROLE_ARN="arn:aws:iam::543032853012:role/connect-lambda-exec-role"
fi

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

  MAX_RETRIES=5
  for ((i=1; i<=MAX_RETRIES; i++)); do
    set +e
    VERSION=$(aws lambda create-function \
      --function-name "$FUNC_NAME" \
      --runtime "$RUNTIME" \
      --role "$ROLE_ARN" \
      --handler "$HANDLER" \
      --zip-file "fileb://$ZIP_FILE" \
      --region "$REGION" \
      --query 'Version' --output text 2>/dev/null)
    STATUS=$?
    set -e

    if [[ "$STATUS" -eq 0 ]]; then
      echo "✅ Lambda created successfully on attempt $i"
      break
    else
      echo "⚠️ Attempt $i failed. Waiting for IAM role to propagate..."
      sleep 10
    fi

    if [[ "$i" -eq "$MAX_RETRIES" ]]; then
      echo "❌ Lambda creation failed after $MAX_RETRIES attempts."
      exit 1
    fi
  done
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
