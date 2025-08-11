import os
import zipfile
import boto3
import argparse
import json
import time
from botocore.exceptions import ClientError

def zip_lambda(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=source_dir)
                zf.write(full_path, arcname)

def wait_and_update_config(lambda_client, function_name, environment_variables, max_retries=10, wait_seconds=5):
    for attempt in range(max_retries):
        try:
            print(f"🔁 Attempt {attempt + 1}: Updating environment variables...")
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': environment_variables}
            )
            print("✅ Environment variables updated successfully.")
            return
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print("⏳ Update in progress. Waiting...")
                time.sleep(wait_seconds)
            else:
                raise e
    raise Exception("❌ Failed to update environment variables after multiple retries.")

def deploy_lambda(lambda_client, function_name, zip_path, role_arn, environment_variables, tags=None):
    with open(zip_path, 'rb') as f:
        code_bytes = f.read()

    try:
        lambda_client.get_function(FunctionName=function_name)
        print(f"🔁 Updating Lambda: {function_name}")

        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=code_bytes
        )

        print(f"📦 Code update successful. Waiting for Lambda to be ready...")
        lambda_client.get_waiter('function_updated').wait(FunctionName=function_name)
        print(f"✅ Lambda is ready.")

        if environment_variables:
            wait_and_update_config(lambda_client, function_name, environment_variables)

        if tags:
            print(f"🏷️ Tagging Lambda: {function_name}")
            lambda_client.tag_resource(
                Resource=f"arn:aws:lambda:{lambda_client.meta.region_name}:{boto3.client('sts').get_caller_identity()['Account']}:function:{function_name}",
                Tags=tags
            )

    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"➕ Creating Lambda: {function_name}")
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': code_bytes},
            Timeout=60,
            MemorySize=128,
            Publish=True,
            Environment={'Variables': environment_variables} if environment_variables else {},
            Tags=tags if tags else {}
        )

        print("⏳ Waiting for Lambda creation to complete...")
        lambda_client.get_waiter('function_active').wait(FunctionName=function_name)
        print(f"✅ Lambda {function_name} is now active.")


def main(env):
    region = os.environ.get("AWS_REGION", "us-east-1")
    lambda_client = boto3.client("lambda", region_name=region)

    with open("config/lambda_config.json") as f:
        all_config = json.load(f)

    if env not in all_config:
        raise Exception(f"❌ No Lambda config found for env: {env}")

    for fn in all_config[env]:
        zip_path = f"{fn['path']}.zip"
        print(f"📦 Zipping {fn['path']} to {zip_path}")
        zip_lambda(fn['path'], zip_path)

        deploy_lambda(
            lambda_client=lambda_client,
            function_name=f"{fn['name']}-{env}",
            zip_path=zip_path,
            role_arn=fn['role_arn'],
            environment_variables=fn.get('environment_variables', {}),
            tags=fn.get('tags')
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, help="Environment (dev/uat/prod)")
    args = parser.parse_args()
    main(args.env)
