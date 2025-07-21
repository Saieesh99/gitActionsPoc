import os
import zipfile
import boto3
import argparse
import json

def zip_lambda(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=source_dir)
                zf.write(full_path, arcname)

def deploy_lambda(lambda_client, function_name, zip_path, role_arn, environment_variables):
    with open(zip_path, 'rb') as f:
        code_bytes = f.read()

    try:
        lambda_client.get_function(FunctionName=function_name)
        print(f"🔁 Updating Lambda: {function_name}")

        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=code_bytes
        )

        print(f"🔁 Updating Lambda: reached here")

        if environment_variables:
            print(f"🔁 Updating Lambda: reached here2")
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': environment_variables}
            )
            print(f"🔁 Updating Lambda: reached here3")

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
            Environment={'Variables': environment_variables} if environment_variables else {}
        )


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
            environment_variables=fn.get('environment_variables', {})
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, help="Environment (dev/uat/prod)")
    args = parser.parse_args()
    main(args.env)
