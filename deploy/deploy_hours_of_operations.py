#!/usr/bin/env python3

import boto3
import argparse
import json
import os
import sys

# 🧾 Parse environment
parser = argparse.ArgumentParser(description="Deploy Hours of Operation with per-HOO tags")
parser.add_argument('--env', required=True, help="Environment (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# 🔄 Load config
config_path = "config/connect_hours_of_operations_config.json"
if not os.path.exists(config_path):
    sys.exit("❌ Config file missing")

with open(config_path, "r") as f:
    config = json.load(f)

if env not in config["environments"]:
    sys.exit(f"❌ Environment '{env}' missing")

env_config = config["environments"][env]
hoo_entries = env_config.get("hours_of_operation", [])
instance_id = config["instance_id"]
region = config.get("region", "us-east-1")

# 🔗 Boto3 client
client = boto3.client("connect", region_name=region)

# 🔍 Fetch existing HOOs
print("🔍 Checking existing Hours of Operation...")
existing_hoos = {}
paginator = client.get_paginator("list_hours_of_operations")
for page in paginator.paginate(InstanceId=instance_id):
    for hoo in page["HoursOfOperationSummaryList"]:
        existing_hoos[hoo["Name"]] = hoo["Id"]

# 🗂 Track HOO ID map
hoo_id_map = {}

# 🚀 Deploy each HOO
for hoo in hoo_entries:
    name = hoo["name"]
    description = hoo.get("description", "")
    time_zone = hoo.get("time_zone", "Asia/Kolkata")
    config_blocks = []

    for block in hoo["config"]:
        config_blocks.append({
            "Day": block["day"],
            "StartTime": {
                "Hours": block["start_time"]["hours"],
                "Minutes": block["start_time"]["minutes"]
            },
            "EndTime": {
                "Hours": block["end_time"]["hours"],
                "Minutes": block["end_time"]["minutes"]
            }
        })

    tags = hoo.get("tags", {})
    if name in existing_hoos:
        hoo_id = existing_hoos[name]
        print(f"✅ HOO '{name}' already exists — reusing ID: {hoo_id}")
        hoo_id_map[name] = hoo_id
        continue

    try:
        print(f"➕ Creating new HOO: {name}")
        response = client.create_hours_of_operation(
            InstanceId=instance_id,
            Name=name,
            Description=description,
            TimeZone=time_zone,
            Config=config_blocks,
            Tags=tags
        )
        hoo_id = response["HoursOfOperationId"]
        print(f"✅ Created HOO '{name}' with ID: {hoo_id}")
        hoo_id_map[name] = hoo_id
    except Exception as e:
        print(f"❌ Failed to create HOO '{name}': {e}")

# 💾 Save output
os.makedirs("output", exist_ok=True)
output_path = f"output/{env}_hoo_ids.json"
with open(output_path, "w") as f:
    json.dump(hoo_id_map, f, indent=2)

print(f"📁 Saved HOO ID map to: {output_path}")
