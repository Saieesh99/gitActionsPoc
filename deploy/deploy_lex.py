import boto3
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--env', required=True)
args = parser.parse_args()

client = boto3.client('lexv2-models')

with open('lex/lex_config.json') as f:
    config = json.load(f)

# Use the bot ID and alias specific to env
bot_id = config[args.env]['bot_id']
bot_alias_id = config[args.env]['alias_id']
locale_id = config[args.env]['locale_id']

# Start Bot build
print(f"🔄 Building Lex Bot for {args.env}")
client.build_bot_locale(
    botId=bot_id,
    botVersion='DRAFT',
    localeId=locale_id
)
