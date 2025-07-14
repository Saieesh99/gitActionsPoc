#!/usr/bin/env python3

import boto3
import json
import argparse
import sys
import os

CONFIG_PATH = "config/eventbridge_config.json"

# 🧾 Load environment-specific config
def load_config(env):
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config file not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    if env not in config["environments"]:
        print(f"❌ Environment '{env}' not found in config.")
        sys.exit(1)

    env_config = config["environments"][env]
    return {
        "region": config.get("region", "us-east-1"),
        "bucket_name": config["bucket_name"],
        "prefix": env_config["prefix"],
        "rule_name": env_config["rule_name"],
        "lambda_arn": env_config["lambda_arn"]
    }

# 🔗 Enable EventBridge on S3 bucket
def enable_s3_eventbridge(bucket_name, region):
    s3 = boto3.client('s3', region_name=region)
    print(f"🔗 Enabling S3 EventBridge notifications on bucket: {bucket_name}...")

    try:
        s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration={
                "EventBridgeConfiguration": {}
            }
        )
        print(f"✅ 'Send to EventBridge' enabled for bucket: {bucket_name}")
    except Exception as e:
        print(f"❌ Failed to enable S3 EventBridge: {str(e)}")
        sys.exit(1)

# 🚀 Main deployment logic
def deploy_eventbridge(env):
    cfg = load_config(env)

    events = boto3.client("events", region_name=cfg["region"])
    lambda_client = boto3.client("lambda", region_name=cfg["region"])

    # Step 1: Enable EventBridge notifications in the S3 bucket
    enable_s3_eventbridge(cfg["bucket_name"], cfg["region"])

    # Step 2: Create EventBridge rule
    event_pattern = {
        "source": ["aws.s3"],
        "detail-type": ["Object Created"],
        "detail": {
            "bucket": {
                "name": [cfg["bucket_name"]]
            },
            "object": {
                "key": [
                    {"prefix": cfg["prefix"]},
                    {"suffix": ".wav"}
                ]
            }
        }
    }

    print(f"📡 Creating EventBridge rule '{cfg['rule_name']}'...")
    rule_resp = events.put_rule(
        Name=cfg["rule_name"],
        EventPattern=json.dumps(event_pattern),
        State="ENABLED",
        Description=f"Trigger Lambda on .wav upload in {cfg['prefix']}"
    )
    rule_arn = rule_resp["RuleArn"]
    print(f"✅ Rule created: {cfg['rule_name']} (ARN: {rule_arn})")

    # Step 3: Add Lambda as a target
    events.put_targets(
        Rule=cfg["rule_name"],
        Targets=[{
            "Id": f"{env}-wav-target",
            "Arn": cfg["lambda_arn"]
        }]
    )

    # Step 4: Allow EventBridge to invoke the Lambda
    try:
        lambda_client.add_permission(
            FunctionName=cfg["lambda_arn"],
            StatementId=f"AllowExecutionFromEventBridge-{env}",
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_arn
        )
        print("🔐 Lambda permission granted to EventBridge")
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️ Lambda permission already exists, skipping...")

    print(f"🚀 Deployment complete for environment: '{env}'")

# 🎯 Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy S3-triggered EventBridge rule to Lambda")
    parser.add_argument("--env", required=True, help="Environment: dev | uat | prod")
    args = parser.parse_args()
    deploy_eventbridge(args.env.lower())
