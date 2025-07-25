#!/usr/bin/env python3

import boto3
import argparse
import json
import sys
import os

# ✅ Parse CLI arguments
parser = argparse.ArgumentParser(description="Deploy Amazon Connect contact flows")
parser.add_argument('--env', required=True, help="Environment to deploy (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load configuration from JSON
config_path = "config/connect_config.json"
if not os.path.exists(config_path):
    print(f"❌ Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, 'r') as f:
    config = json.load(f)

if env not in config["environments"]:
    print(f"❌ Unknown environment '{env}' in config.")
    sys.exit(1)

# ✅ Pull environment config
env_config = config["environments"][env]
flows = env_config.get("flows", [])
instance_id = config.get("instance_id")
region = config.get("region", "us-east-1")

# ✅ Boto3 client
client = boto3.client('connect', region_name=region)

# ✅ List existing contact flows
print("🔍 Fetching existing contact flows...")
response = client.list_contact_flows(InstanceId=instance_id)
existing_flows = {f["Name"]: f["Id"] for f in response.get("ContactFlowSummaryList", [])}

# ✅ Track deployed flow IDs
deployed_flows = {}

# ✅ Deploy each flow
for flow in flows:
    flow_name = flow["flow_name"]
    flow_file = flow["flow_file"]

    if not os.path.exists(flow_file):
        print(f"❌ Contact flow file not found: {flow_file}")
        continue

    with open(flow_file, 'r') as f:
        content = f.read()

    if flow_name in existing_flows:
        flow_id = existing_flows[flow_name]
        print(f"🔄 Updating contact flow '{flow_name}' (ID: {flow_id})...")
        client.update_contact_flow_content(
            InstanceId=instance_id,
            ContactFlowId=flow_id,
            Content=content
        )
    else:
        print(f"➕ Creating new contact flow '{flow_name}'...")
        result = client.create_contact_flow(
            InstanceId=instance_id,
            Name=flow_name,
            Type="CONTACT_FLOW",
            Content=content,
            Description=f"{flow_name} flow created via script"
        )
        flow_id = result['ContactFlowId']
        print(f"✅ Created contact flow ID: {flow_id}")

    # Save to deployed flows dict
    deployed_flows[flow_name] = flow_id

# ✅ Write output to file
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f"{env}_callflow_ids.json")

with open(output_file, 'w') as f:
    json.dump(deployed_flows, f, indent=2)

print(f"📝 Contact flow IDs written to: {output_file}")
print(f"🚀 Contact flow deployment complete for '{env}'.")
