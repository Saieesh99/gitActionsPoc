#!/usr/bin/env python3

import boto3
import os
import sys
import json
import mimetypes
import argparse
from pathlib import Path
from botocore.exceptions import ClientError

# ✅ Parse arguments
parser = argparse.ArgumentParser(description="Deploy prompts to Amazon Connect")
parser.add_argument("--env", required=True, help="Environment (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load config
config_path = "config/connect_prompts_config.json"
if not os.path.exists(config_path):
    print(f"❌ Config file not found: {config_path}")
    sys.exit(1)

with open(config_path) as f:
    config = json.load(f)

if env not in config["environments"]:
    print(f"❌ Unknown environment '{env}' in config.")
    sys.exit(1)

env_config = config["environments"][env]
instance_id = config["instance_id"]
region = config.get("region", "us-east-1")
bucket_name = env_config["s3_bucket"]
prompt_tags_config = env_config.get("prompts", {})
prompt_folder = f"prompts/{env}"

# ✅ AWS Clients
s3 = boto3.client("s3", region_name=region)
connect = boto3.client("connect", region_name=region)

def s3_file_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise

def convert_tags_to_s3_format(tags_dict):
    return [{"Key": k, "Value": v} for k, v in tags_dict.items()]

# ✅ Upload prompts and register
def upload_and_register_prompts():
    for root, _, files in os.walk(prompt_folder):
        for file in files:
            if not file.lower().endswith(".wav"):
                continue

            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, prompt_folder)
            s3_key = relative_path.replace("\\", "/")  # Normalize path
            prompt_name = Path(file).stem
            s3_uri = f"s3://{bucket_name}/{s3_key}"

            top_level_folder = s3_key.split("/")[0]
            tags = prompt_tags_config.get(top_level_folder, {}).get("tags", {})
            s3_tags = convert_tags_to_s3_format(tags)

            # ✅ Upload to S3 if file doesn't exist
            if s3_file_exists(bucket_name, s3_key):
                print(f"⏩ Skipping upload. File already exists in S3: '{s3_key}'")
            else:
                try:
                    s3.upload_file(
                        Filename=full_path,
                        Bucket=bucket_name,
                        Key=s3_key,
                        ExtraArgs={"ContentType": mimetypes.guess_type(file)[0] or "audio/wav"}
                    )
                    if s3_tags:
                        s3.put_object_tagging(
                            Bucket=bucket_name,
                            Key=s3_key,
                            Tagging={"TagSet": s3_tags}
                        )
                    print(f"☁️ Uploaded and tagged '{s3_key}' to bucket '{bucket_name}'")
                except Exception as e:
                    print(f"❌ Error uploading '{s3_key}': {e}")
                    continue

            # ✅ Register prompt with Amazon Connect
            try:
                connect.create_prompt(
                    InstanceId=instance_id,
                    Name=prompt_name,
                    Description=f"Uploaded prompt: {prompt_name}",
                    S3Uri=s3_uri,
                    Tags=tags
                )
                print(f"✅ Registered prompt '{prompt_name}' in Amazon Connect")
            except connect.exceptions.DuplicateResourceException:
                print(f"⚠️ Prompt '{prompt_name}' already exists in Connect.")
            except Exception as e:
                print(f"❌ Error creating prompt '{prompt_name}': {e}")

# ✅ Start deployment
upload_and_register_prompts()
print(f"🚀 Prompt deployment complete for '{env}' environment.")
