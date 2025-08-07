#!/usr/bin/env python3

import boto3
import json
import os
import sys
import argparse
from botocore.exceptions import ClientError

# ✅ Parse CLI argument
parser = argparse.ArgumentParser(description="Deploy DynamoDB tables per environment.")
parser.add_argument("--env", required=True, help="Environment (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load config
config_path = "config/dynamodb_config.json"
if not os.path.exists(config_path):
    print(f"❌ Config file not found: {config_path}")
    sys.exit(1)

with open(config_path) as f:
    config = json.load(f)

if env not in config["environments"]:
    print(f"❌ Unknown environment '{env}' in config.")
    sys.exit(1)

instance_id = config["instance_id"]
region = config.get("region", "us-east-1")
env_tables = config["environments"][env]["tables"]

# ✅ AWS client
dynamodb = boto3.client("dynamodb", region_name=region)

# ✅ Convert tag dict to AWS format
def convert_tags(tag_dict):
    return [{"Key": k, "Value": v} for k, v in tag_dict.items()]

# ✅ Deploy DynamoDB Tables
for table in env_tables:
    table_name = table["name"]
    try:
        dynamodb.describe_table(TableName=table_name)
        print(f"⏩ Table '{table_name}' already exists. Skipping.")
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"📦 Creating table: {table_name}")
        try:
            dynamodb.create_table(
                TableName=table_name,
                AttributeDefinitions=table["attributes"],
                KeySchema=table["key_schema"],
                BillingMode=table.get("billing_mode", "PAY_PER_REQUEST"),
                Tags=convert_tags(table.get("tags", {}))
            )
            print(f"✅ Table '{table_name}' created successfully.")
        except ClientError as e:
            print(f"❌ Error creating table '{table_name}': {e}")
    except ClientError as e:
        print(f"❌ Error describing table '{table_name}': {e}")

print(f"🚀 DynamoDB table deployment complete for '{env}' environment.")
