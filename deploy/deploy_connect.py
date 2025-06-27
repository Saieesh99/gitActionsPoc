import boto3
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--env', required=True)
args = parser.parse_args()

instance_id = "<your_connect_instance_id>"
contact_flow_id = "<your_flow_id_per_env>"

with open(f"connect/contact_flow.json") as f:
    content = f.read()

client = boto3.client('connect')
response = client.update_contact_flow_content(
    InstanceId=instance_id,
    ContactFlowId=contact_flow_id,
    Content=content
)

print(f"✅ Updated contact flow for {args.env}")
