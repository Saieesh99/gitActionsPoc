#!/usr/bin/env python3

import boto3
import argparse
import json
import time
import sys
from botocore.exceptions import ClientError

def wait_for_bot_available(client, bot_id):
    print("\u23f3 Waiting for bot to become AVAILABLE...")
    while True:
        desc = client.describe_bot(botId=bot_id)
        status = desc['botStatus']
        print(f"   \u21aa Current bot status: {status}")
        if status == "Available":
            break
        elif status == "Failed":
            sys.exit("\u274c Bot creation failed.")
        time.sleep(5)

def wait_for_locale_ready(client, bot_id, locale_id):
    print("\u23f3 Waiting for locale to be ReadyBeforeBuild...")
    while True:
        status = client.describe_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id
        )['botLocaleStatus']
        print(f"   \u21aa Current locale status: {status}")
        if status in ["ReadyBeforeBuild", "NotBuilt"]:
            break
        elif status == "Failed":
            sys.exit("\u274c Locale creation failed.")
        time.sleep(5)

def wait_for_locale_build(client, bot_id, locale_id):
    print("\u23f1 Waiting for build to complete...")
    while True:
        status = client.describe_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id
        )['botLocaleStatus']
        print(f"   \u21aa Current status: {status}")
        if status in ['Built', 'Failed']:
            return status
        time.sleep(5)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', required=True)
    args = parser.parse_args()

    with open('lex/lex_config.json') as f:
        config = json.load(f)

    env_config = config.get(args.env)
    if not env_config:
        sys.exit(f"\u274c No Lex config found for environment '{args.env}'")

    bot_name = env_config['bot_name']
    locale_id = env_config['locale_id']
    bot_alias_name = env_config['alias_name']
    role_arn = env_config['lex_role_arn']

    client = boto3.client('lexv2-models')

    # 1. Check or create bot
    bots = client.list_bots()['botSummaries']
    bot = next((b for b in bots if b['botName'] == bot_name), None)

    if bot:
        bot_id = bot['botId']
        print(f"\u2705 Bot '{bot_name}' exists (ID: {bot_id})")
    else:
        print(f"\u2795 Creating bot '{bot_name}'...")
        response = client.create_bot(
            botName=bot_name,
            roleArn=role_arn,
            dataPrivacy={"childDirected": False},
            idleSessionTTLInSeconds=300
        )
        bot_id = response['botId']
        print(f"\u2705 Created bot: {bot_id}")
        wait_for_bot_available(client, bot_id)

    # 2. Check or create locale
    locales = client.list_bot_locales(botId=bot_id, botVersion='DRAFT')['botLocaleSummaries']
    locale = next((l for l in locales if l['localeId'] == locale_id), None)

    if not locale:
        print(f"\u2795 Creating locale '{locale_id}'...")
        client.create_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id,
            description=f"{args.env} locale created via script",
            nluIntentConfidenceThreshold=0.40
        )

    wait_for_locale_ready(client, bot_id, locale_id)

    # 3. Ensure a sample intent exists
    intents = client.list_intents(botId=bot_id, botVersion='DRAFT', localeId=locale_id)['intentSummaries']
    intent_exists = any(i['intentName'] == 'HelloIntent' for i in intents)

    if not intent_exists:
        print("\u2795 Adding fallback HelloIntent...")
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
        print("\u2705 HelloIntent added.")
        client.create_intent(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id,
            intentName='SecondHelloIntent',
            sampleUtterances=[
                {'utterance': 'second hi'},
                {'utterance': 'second hello'},
                {'utterance': 'second hey there'}
            ]
        )
        print("\u2705 Second HelloIntent added.")
    else:
        print("\u2705 HelloIntent already exists.")

    # 4. Build locale
    print(f"\u1f504 Building locale '{locale_id}'...")
    client.build_bot_locale(botId=bot_id, botVersion='DRAFT', localeId=locale_id)

    build_status = wait_for_locale_build(client, bot_id, locale_id)
    if build_status == 'Failed':
        sys.exit("\u274c Bot build failed.")
    print("\u2705 Locale built successfully.")

    # # 5. Create or update alias
    # aliases = client.list_bot_aliases(botId=bot_id)['botAliasSummaries']
    # alias = next((a for a in aliases if a['botAliasName'] == bot_alias_name), None)

    # if alias:
    #     print(f"\u1f501 Updating alias '{bot_alias_name}'...")
    #     client.update_bot_alias(
    #         botAliasId=alias['botAliasId'],
    #         botId=bot_id,
    #         botAliasName=bot_alias_name,
    #         botVersion='DRAFT',
    #         localeSettings={locale_id: {'enabled': True}}
    #     )
    # else:
    #     print(f"\u2795 Creating alias '{bot_alias_name}'...")
    #     # client.create_bot_alias(
    #     #     botAliasName=bot_alias_name,
    #     #     botId=bot_id,
    #     #     botVersion='DRAFT',
    #     #     localeSettings={locale_id: {'enabled': True}}
    #     # )
    #     client.create_bot_alias(
    #         botAliasName=bot_alias_name,
    #         botId=bot_id,
    #         botVersion='DRAFT',
    #         botAliasLocaleSettings=alias_settings
    #     )

    # print(f"\U0001f680 Lex bot deployed successfully for environment: {args.env}")

if __name__ == '__main__':
    main()