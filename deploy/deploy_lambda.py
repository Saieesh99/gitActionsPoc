# deploy_lambda.py
import boto3
import zipfile
import os

LAMBDA_NAME = "voicemail_email_lambda"
ZIP_NAME = "lambda_email.zip"
LAMBDA_HANDLER = "lambda_function.lambda_handler"
ROLE_ARN = "arn:aws:iam::<account-id>:role/lambda_email_role"

def create_zip():
    with zipfile.ZipFile(ZIP_NAME, 'w') as zipf:
        zipf.write('lambda_email/lambda_function.py', arcname='lambda_function.py')
    print(f"{ZIP_NAME} created")

def deploy_lambda():
    create_zip()
    client = boto3.client('lambda')
    with open(ZIP_NAME, 'rb') as f:
        zipped_code = f.read()

    try:
        client.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=zipped_code,
            Publish=True
        )
        print("Lambda code updated.")
    except client.exceptions.ResourceNotFoundException:
        client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.12",
            Role=ROLE_ARN,
            Handler=LAMBDA_HANDLER,
            Code={'ZipFile': zipped_code},
            Environment={
                'Variables': {
                    'SES_FROM': "from@example.com",
                    'SES_TO': "to@example.com"
                }
            },
            Timeout=30,
            MemorySize=128
        )
        print("Lambda function created.")

if __name__ == "__main__":
    deploy_lambda()
