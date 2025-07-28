#!/usr/bin/env python3

import boto3
import argparse
import json
import os
import sys

# ✅ Parse environment argument
parser = argparse.ArgumentParser(description="Deploy Amazon Connect routing profiles")
parser.add_argument("--env", required=True, help="Environment to deploy (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load main config
config_path = "config/connect_routing_profiles_config.json"
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
profiles = env_config.get("routing_profiles", [])

# ✅ Load queue ID mappings
queue_id_path = f"output/{env}_queue_ids.json"
if not os.path.exists(queue_id_path):
    print(f"❌ Queue ID mapping file not found: {queue_id_path}")
    sys.exit(1)

with open(queue_id_path, "r") as f:
    queue_id_map = json.load(f)

# ✅ AWS client
client = boto3.client("connect", region_name=region)

# ✅ Helper: Get routing profile ID by name
def get_routing_profile_id_by_name(name):
    paginator = client.get_paginator('list_routing_profiles')
    for page in paginator.paginate(InstanceId=instance_id):
        for profile in page['RoutingProfileSummaryList']:
            if profile['Name'] == name:
                return profile['Id']
    return None

# ✅ Deploy routing profiles
for profile in profiles:
    name = profile["name"]
    description = profile.get("description", "")
    default_queue = profile["default_queue"]
    queue_configs = profile.get("queues", [])
    tags = profile.get("tags", {})

    if default_queue not in queue_id_map:
        print(f"❌ Default queue '{default_queue}' not found in {queue_id_path}")
        continue
    default_queue_id = queue_id_map[default_queue]

    queue_configs_with_ids = []
    for qc in queue_configs:
        queue_name = qc["queue_name"]
        priority = qc.get("priority", 1)
        delay = qc.get("delay", 0)
        channels = qc.get("channel", "VOICE")
        if isinstance(channels, str):
            channels = [channels]

        if queue_name not in queue_id_map:
            print(f"⚠️ Queue '{queue_name}' not found in queue ID mapping.")
            continue

        for channel in channels:
            queue_configs_with_ids.append({
                "QueueReference": {
                    "QueueId": queue_id_map[queue_name],
                    "Channel": channel
                },
                "Priority": priority,
                "Delay": delay
            })

    existing_id = get_routing_profile_id_by_name(name)

    try:
        if existing_id:
            # ✅ Update existing routing profile
            client.update_routing_profile_name(
                InstanceId=instance_id,
                RoutingProfileId=existing_id,
                Name=name,
                Description=description
            )

            client.update_routing_profile_default_outbound_queue(
                InstanceId=instance_id,
                RoutingProfileId=existing_id,
                DefaultOutboundQueueId=default_queue_id
            )

            client.update_routing_profile_queues(
                InstanceId=instance_id,
                RoutingProfileId=existing_id,
                QueueConfigs=queue_configs_with_ids
            )

            # Optional: update tags (not supported via update API, you'd have to tag_resource)
            client.tag_resource(
                resourceArn=f"arn:aws:connect:{region}:{boto3.client('sts').get_caller_identity()['Account']}:instance/{instance_id}/routing-profile/{existing_id}",
                tags=tags
            )

            print(f"🔁 Updated routing profile '{name}' (ID: {existing_id})")
        else:
            # ✅ Create new routing profile
            response = client.create_routing_profile(
                InstanceId=instance_id,
                Name=name,
                Description=description,
                DefaultOutboundQueueId=default_queue_id,
                MediaConcurrencies=[{"Channel": "VOICE", "Concurrency": 1}],
                QueueConfigs=queue_configs_with_ids,
                Tags=tags
            )
            print(f"✅ Created routing profile '{name}' (ID: {response['RoutingProfileId']})")

    except Exception as e:
        print(f"❌ Error deploying routing profile '{name}': {e}")

print(f"🚀 Routing profile deployment complete for '{env}'.")
