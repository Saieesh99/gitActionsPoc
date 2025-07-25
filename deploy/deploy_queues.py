#!/usr/bin/env python3

import boto3
import argparse
import json
import sys
import os

# ✅ Parse arguments
parser = argparse.ArgumentParser(description="Deploy Amazon Connect queues")
parser.add_argument("--env", required=True, help="Environment to deploy (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load config
config_path = "config/connect_queues_config.json"
if not os.path.exists(config_path):
    print(f"❌ Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, "r") as f:
    config = json.load(f)

if env not in config["environments"]:
    print(f"❌ Unknown environment '{env}' in config.")
    sys.exit(1)

instance_id = config["instance_id"]
region = config.get("region", "us-east-1")
env_config = config["environments"][env]
queue_configs = env_config.get("queues", [])

# ✅ Load HOO ID mappings
hoo_path = f"output/{env}_hoo_ids.json"
if not os.path.exists(hoo_path):
    print(f"❌ HOO mapping file not found: {hoo_path}")
    sys.exit(1)

with open(hoo_path, "r") as f:
    hoo_id_map = json.load(f)

# ✅ Boto3 client
client = boto3.client("connect", region_name=region)
sts_client = boto3.client("sts")

# ✅ Fetch existing queues with names using describe_queue
print("🔍 Fetching existing queues...")
existing_queues = {}
paginator = client.get_paginator("list_queues")
for page in paginator.paginate(InstanceId=instance_id):
    for queue in page.get("QueueSummaryList", []):
        queue_id = queue["Id"]
        try:
            details = client.describe_queue(InstanceId=instance_id, QueueId=queue_id)
            queue_name = details["Queue"]["Name"]
            existing_queues[queue_name] = queue_id
        except Exception as e:
            print(f"⚠️ Failed to describe queue {queue_id}: {e}")

# ✅ Create or update queues
for q in queue_configs:
    queue_name = q["name"]
    description = q.get("description", "")
    max_contacts = q.get("max_contacts", 10)
    hoo_name = q["hours_of_operation"]
    tags = q.get("tags", {})

    outbound_cfg = q.get("outbound_caller_config", {})
    raw_flow_key = outbound_cfg.get("OutboundFlowId", "")
    print("instance_id ",instance_id)

    outbound_caller_config = {
        "OutboundCallerIdName": outbound_cfg.get("OutboundCallerIdName", ""),
        "OutboundCallerIdNumberId": outbound_cfg.get("OutboundCallerIdNumberId", ""),
        "OutboundFlowId": outbound_cfg.get("OutboundFlowId", "")
    }

    hoo_id = hoo_id_map.get(hoo_name)
    if not hoo_id:
        print(f"❌ HOO '{hoo_name}' not found in mapping file.")
        continue

    print("queue_name ",queue_name)
    print("existing_queues ",existing_queues)
    if queue_name in existing_queues:
        queue_id = existing_queues[queue_name]
        print(f"🔄 Updating queue: {queue_name} (ID: {queue_id})")

        try:
            client.update_queue_name(
                InstanceId=instance_id,
                QueueId=queue_id,
                Name=queue_name,
                Description=description
            )

            client.update_queue_hours_of_operation(
                InstanceId=instance_id,
                QueueId=queue_id,
                HoursOfOperationId=hoo_id
            )

            client.update_queue_max_contacts(
                InstanceId=instance_id,
                QueueId=queue_id,
                MaxContacts=max_contacts
            )

            client.update_queue_outbound_caller_config(
                InstanceId=instance_id,
                QueueId=queue_id,
                OutboundCallerConfig=outbound_caller_config
            )

            if tags:
                account_id = sts_client.get_caller_identity()["Account"]
                queue_arn = f"arn:aws:connect:{region}:{account_id}:instance/{instance_id}/queue/{queue_id}"
                client.tag_resource(resourceArn=queue_arn, tags=tags)

        except Exception as e:
            print(f"❌ Error updating queue '{queue_name}': {e}")
    else:
        print(f"➕ Creating queue: {queue_name}")
        try:
            response = client.create_queue(
                InstanceId=instance_id,
                Name=queue_name,
                Description=description,
                OutboundCallerConfig=outbound_caller_config,
                HoursOfOperationId=hoo_id,
                MaxContacts=max_contacts,
                Tags=tags
            )
            print(f"✅ Created queue ID: {response['QueueId']}")
        except client.exceptions.InvalidParameterException as e:
            print(f"❌ InvalidParameterException while creating queue '{queue_name}': {e}")
        except client.exceptions.DuplicateResourceException as e:
            print(f"⚠️ Queue '{queue_name}' already exists (DuplicateResourceException).")
        except Exception as e:
            print(f"❌ Unexpected error while creating queue '{queue_name}': {str(e)}")

print(f"🚀 Queue deployment complete for '{env}'.")
