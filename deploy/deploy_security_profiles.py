#!/usr/bin/env python3

import boto3
import argparse
import json
import os
import sys

# ✅ Parse environment argument
parser = argparse.ArgumentParser(description="Deploy Amazon Connect security profiles")
parser.add_argument("--env", required=True, help="Environment to deploy (dev | uat | prod)")
args = parser.parse_args()
env = args.env.lower()

# ✅ Load main config
config_path = "config/connect_security_profiles_config.json"
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
env_profiles = config["environments"][env].get("security_profiles", [])

# ✅ AWS clients
client = boto3.client("connect", region_name=region)
sts_client = boto3.client("sts")

# ✅ Get account ID for ARN generation
account_id = sts_client.get_caller_identity()["Account"]

# ✅ Fetch existing security profiles
existing_profiles = {}
paginator = client.get_paginator("list_security_profiles")
for page in paginator.paginate(InstanceId=instance_id):
    for sp in page["SecurityProfileSummaryList"]:
        existing_profiles[sp["Name"]] = sp["Id"]

# ✅ Deploy security profiles
for profile in env_profiles:
    name = profile["name"]
    description = profile.get("description", "")
    permissions = profile.get("permissions", [])
    tags = profile.get("tags", {})

    if name in existing_profiles:
        security_profile_id = existing_profiles[name]
        print(f"🔄 Updating security profile '{name}' (ID: {security_profile_id})")

        try:
            client.update_security_profile(
                InstanceId=instance_id,
                SecurityProfileId=security_profile_id,
                Description=description,
                Permissions=permissions
            )

            # ✅ Add Tags
            profile_arn = f"arn:aws:connect:{region}:{account_id}:instance/{instance_id}/security-profile/{security_profile_id}"
            if tags:
                client.tag_resource(ResourceArn=profile_arn, Tags=tags)

            print(f"✅ Updated security profile '{name}'")
        except Exception as e:
            print(f"❌ Error updating security profile '{name}': {e}")
    else:
        print(f"➕ Creating security profile '{name}'")

        try:
            print("instance_id ",instance_id)
            print("name ",name)
            print("description ",description)
            print("permissions ",permissions)
            print("tags ",tags)

            response = client.create_security_profile(
                InstanceId="125d4a4f-946b-4b2d-aae7-7f7ee3be569c",
                SecurityProfileName="Supervisor-DEV",
                Description="Supervisor role with limited safe permissions",
                Permissions= ['BasicAgentAccess', 'ContactSearch', 'ViewContactTraceRecords', 'OutboundCallAccess'],
                Tags={'Environment': 'dev', 'Team': 'Supervisors'}
            )

            response = client.create_security_profile(
                InstanceId=instance_id,
                SecurityProfileName=name,
                Description=description,
                Permissions=permissions,
                Tags=tags
            )
            print(f"✅ Created security profile '{name}' (ID: {response['SecurityProfileId']})")
        except Exception as e:
            print(f"❌ Error creating security profile '{name}': {e}")

print(f"🚀 Security profile deployment complete for '{env}'.")
