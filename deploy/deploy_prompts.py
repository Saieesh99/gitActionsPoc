#!/usr/bin/env python3

import boto3
import os
import sys
import json
import argparse
from botocore.exceptions import ClientError

# ✅ Parse CLI arguments
parser = argparse.ArgumentParser(description="Register prompts from S3 to Amazon Connect")
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
prompt_configs = env_config.get("prompts", {})

# ✅ AWS clients
s3 = boto3.client("s3", region_name=region)
connect = boto3.client("connect", region_name=region)

def prompt_exists_in_connect(prompt_name):
    try:
        paginator = connect.get_paginator("list_prompts")
        for page in paginator.paginate(InstanceId=instance_id):
            for prompt in page.get("PromptSummaryList", []):
                if prompt["Name"] == prompt_name:
                    return True
        return False
    except Exception as e:
        print(f"❌ Error checking prompt '{prompt_name}' existence: {e}")
        return False

def s3_file_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise

# ✅ Register prompts in Connect from S3
def register_prompts_from_s3():
    for prompt_name, details in prompt_configs.items():
        s3_key = details.get("s3_key")
        tags = details.get("tags", {})
        if not s3_key:
            print(f"⚠️ Skipping '{prompt_name}': No 's3_key' specified.")
            continue

        if not s3_file_exists(bucket_name, s3_key):
            print(f"❌ File not found in S3: s3://{bucket_name}/{s3_key}")
            continue

        s3_uri = f"s3://{bucket_name}/{s3_key}"

        if prompt_exists_in_connect(prompt_name):
            print(f"⏩ Prompt '{prompt_name}' already exists in Amazon Connect.")
            continue

        try:
            connect.create_prompt(
                InstanceId=instance_id,
                Name=prompt_name,
                Description=f"Registered prompt from S3: {prompt_name}",
                S3Uri=s3_uri,
                Tags=tags
            )
            print(f"✅ Registered prompt '{prompt_name}' from S3.")
        except Exception as e:
            print(f"❌ Failed to register prompt '{prompt_name}': {e}")

# ✅ Start
register_prompts_from_s3()
print(f"🚀 Prompt deployment complete for '{env}' environment.")
