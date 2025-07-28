#!/usr/bin/env python3

import boto3
import argparse
import json
import os
import sys

# ✅ Parse environment argument
parser = argparse.ArgumentParser(description="Deploy Amazon Connect agent statuses")
parser.add_argument("--env", required=True, help="Environment to deploy (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load main config
config_path = "config/connect_agent_status_config.json"
if not os.path.exists(config_path):
    print(f"❌ Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, "r") as f:
    config = json.load(f)

if env not in config["environments"]:
    print(f"❌ Unknown environment '{env}' in config.")
    sys.exit(1)

region = config.get("region", "us-east-1")
instance_id = config["instance_id"]
statuses = config["environments"][env].get("agent_statuses", [])

# ✅ AWS clients
client = boto3.client("connect", region_name=region)
sts_client = boto3.client("sts")

# ✅ Fetch existing agent statuses to avoid duplicates
existing_statuses = client.list_agent_statuses(
    InstanceId=instance_id,
    AgentStatusTypes=["ENABLED"]
).get("AgentStatusSummaryList", [])

existing_map = {s["Name"]: s["Id"] for s in existing_statuses}

# ✅ Deploy agent statuses
for status in statuses:
    name = status["name"]
    description = status.get("description", "")
    state = status.get("state", "OFFLINE")
    display_order = status.get("display_order", 1)
    tags = status.get("tags", {})

    if name in existing_map:
        agent_status_id = existing_map[name]
        print(f"🔄 Updating agent status '{name}' (ID: {agent_status_id})")
        try:
            client.update_agent_status(
                InstanceId=instance_id,
                AgentStatusId=agent_status_id,
                Name=name,
                Description=description,
                State=state,
                DisplayOrder=display_order
            )

            # ✅ Tagging skipped during update due to unsupported ARN for agent-status
            print(f"✅ Updated agent status '{name}'")
        except Exception as e:
            print(f"❌ Error updating agent status '{name}': {e}")
    else:
        print(f"➕ Creating agent status '{name}'")
        try:
            response = client.create_agent_status(
                InstanceId=instance_id,
                Name=name,
                Description=description,
                State=state,
                DisplayOrder=display_order,
                Tags=tags
            )
            print(f"✅ Created agent status '{name}' (ID: {response['AgentStatusId']})")
        except Exception as e:
            print(f"❌ Error creating agent status '{name}': {e}")

print(f"🚀 Agent status deployment complete for '{env}'.")
