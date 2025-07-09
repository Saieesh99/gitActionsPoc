#!/usr/bin/env python3

import boto3
import argparse
import json
import sys

# 🔧 Configure this map based on your environments
CONTACT_FLOW_NAMES = {
    "dev": "test-dev",
    "uat": "test-uat",
    "prod": "test-prod"
}

# 🔄 Map flow type if needed (usually "CONTACT_FLOW")
CONTACT_FLOW_TYPE = "CONTACT_FLOW"

# 📦 Parse --env argument
parser = argparse.ArgumentParser()
parser.add_argument('--env', required=True)
args = parser.parse_args()

# 🧭 Set instance ID and contact flow name
instance_id = "125d4a4f-946b-4b2d-aae7-7f7ee3be569c"
flow_name = CONTACT_FLOW_NAMES.get(args.env)

if not flow_name:
    print(f"❌ Unknown environment '{args.env}'. Please define it in CONTACT_FLOW_NAMES.")
    sys.exit(1)

# 📂 Load flow content (JSON string)
with open("connect/contact_flow.json") as f:
    content = f.read()

import os

region = os.getenv("AWS_REGION", "us-east-1")
client = boto3.client('connect', region_name=region)

# 🔍 Find existing contact flow by name
response = client.list_contact_flows(InstanceId=instance_id)
flows = response.get("ContactFlowSummaryList", [])
matching_flow = next((f for f in flows if f["Name"] == flow_name), None)

if matching_flow:
    contact_flow_id = matching_flow["Id"]
    print(f"🔄 Updating existing contact flow '{flow_name}' (ID: {contact_flow_id})...")
    client.update_contact_flow_content(
        InstanceId=instance_id,
        ContactFlowId=contact_flow_id,
        Content=content
    )
else:
    print(f"➕ Contact flow '{flow_name}' not found. Creating new one...")
    created = client.create_contact_flow(
        InstanceId=instance_id,
        Name=flow_name,
        Type=CONTACT_FLOW_TYPE,
        Content=content,
        Description=f"{flow_name} flow created via deploy script"
    )
    contact_flow_id = created["ContactFlowId"]
    print(f"✅ Created contact flow '{flow_name}' (ID: {contact_flow_id})")

print(f"🚀 Contact flow for '{args.env}' environment is ready.")
