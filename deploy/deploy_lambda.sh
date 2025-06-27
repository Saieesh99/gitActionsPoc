#!/bin/bash
ENV=$1
ZIP_FILE=lambda_$ENV.zip
FUNC_NAME="my-lex-lambda"

cd lambda
zip -r9 ../$ZIP_FILE .
cd ..

# Upload the code and publish a new version
echo "📦 Uploading and publishing new Lambda version..."
VERSION=$(aws lambda update-function-code \
  --function-name $FUNC_NAME \
  --zip-file fileb://$ZIP_FILE \
  --publish \
  --query 'Version' --output text)

echo "✅ Published version: $VERSION"

# Create or update alias
ALIAS_EXISTS=$(aws lambda list-aliases --function-name $FUNC_NAME --query "Aliases[?Name=='$ENV'] | [0]" --output text)

if [ "$ALIAS_EXISTS" == "None" ]; then
  echo "🔧 Creating alias '$ENV' for version $VERSION"
  aws lambda create-alias \
    --function-name $FUNC_NAME \
    --name $ENV \
    --function-version $VERSION
else
  echo "🔁 Updating alias '$ENV' to version $VERSION"
  aws lambda update-alias \
    --function-name $FUNC_NAME \
    --name $ENV \
    --function-version $VERSION
fi
