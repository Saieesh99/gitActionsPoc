#!/usr/bin/env python3

import boto3
import argparse
import json
import time
import sys
import os
from botocore.exceptions import ClientError

import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

def wait_for_bot_available(client, bot_id):
    print("⏳ Waiting for bot to become AVAILABLE...")
    while True:
        desc = client.describe_bot(botId=bot_id)
        status = desc['botStatus']
        print(f"   ↪ Current bot status: {status}")
        if status == "Available":
            break
        elif status == "Failed":
            sys.exit("❌ Bot creation failed.")
        time.sleep(5)

def wait_for_locale_ready(client, bot_id, locale_id):
    print("⏳ Waiting for locale to be ReadyBeforeBuild...")
    while True:
        status = client.describe_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id
        )['botLocaleStatus']
        print(f"   ↪ Current locale status: {status}")
        if status in ["ReadyBeforeBuild", "NotBuilt", "Built"]:
            break
        elif status == "Failed":
            sys.exit("❌ Locale creation failed.")
        time.sleep(5)

def wait_for_locale_build(client, bot_id, locale_id):
    print("⏱️ Waiting for build to complete...")
    while True:
        status = client.describe_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id
        )['botLocaleStatus']
        print(f"   ↪ Current status: {status}")
        if status in ['Built', 'Failed']:
            return status
        time.sleep(5)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bot', required=True, help="Bot directory name (e.g. bot1)")
    parser.add_argument('--env', required=True, help="Environment (e.g. dev, qa, prod)")
    args = parser.parse_args()

    bot_dir = f'lex/{args.bot}'
    config_path = os.path.join(bot_dir, 'lex_config.json')

    if not os.path.exists(config_path):
        sys.exit(f"❌ Config file not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    env_config = config.get(args.env)
    if not env_config:
        sys.exit(f"❌ No config found for env '{args.env}' in {config_path}")

    bot_name = env_config['bot_name']
    locale_id = env_config['locale_id']
    alias_name = env_config['alias_name']
    role_arn = env_config['lex_role_arn']

    region = os.getenv("AWS_REGION", "us-east-1")
    client = boto3.client('lexv2-models', region_name=region)

    bots = client.list_bots()['botSummaries']
    bot = next((b for b in bots if b['botName'] == bot_name), None)

    if bot:
        bot_id = bot['botId']
        print(f"✅ Bot '{bot_name}' exists (ID: {bot_id})")
    else:
        print(f"➕ Creating bot qq'{bot_name}'...")
        response = client.create_bot(
            botName=bot_name,
            roleArn=role_arn,
            dataPrivacy={"childDirected": False},
            idleSessionTTLInSeconds=300
        )
        bot_id = response['botId']
        print(f"✅ Created bot ID: {bot_id}")
        wait_for_bot_available(client, bot_id)

    locales = client.list_bot_locales(botId=bot_id, botVersion='DRAFT')['botLocaleSummaries']
    locale = next((l for l in locales if l['localeId'] == locale_id), None)

    if not locale:
        print(f"➕ Creating locale '{locale_id}'...")
        client.create_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id,
            description=f"{args.env} locale created via script",
            nluIntentConfidenceThreshold=0.40
        )

    wait_for_locale_ready(client, bot_id, locale_id)

    intents = client.list_intents(botId=bot_id, botVersion='DRAFT', localeId=locale_id)['intentSummaries']
    if not any(i['intentName'] == 'HelloIntent' for i in intents):
        print("➕ Adding HelloIntent...")
        client.create_intent(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id,
            intentName='HelloIntent',
            sampleUtterances=[
                {'utterance': 'hi'},
                {'utterance': 'hello'},
                {'utterance': 'hey there'}
            ]
        )
        print("✅ HelloIntent added.")

    print(f"🔄 Building locale '{locale_id}'...")
    client.build_bot_locale(botId=bot_id, botVersion='DRAFT', localeId=locale_id)
    build_status = wait_for_locale_build(client, bot_id, locale_id)
    if build_status == 'Failed':
        sys.exit("❌ Bot build failed.")
    print("✅ Locale built successfully.")

if __name__ == '__main__':
    main()
