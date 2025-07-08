import boto3
import json
import time
import sys
import os
import argparse
import subprocess
import requests

ZIP_DIR_TEMPLATE = "lex/{bot}/exported/{env}"
CONFIG_FILE_TEMPLATE = "lex/{bot}/lex_config.json"
MAX_ATTEMPTS = 20
SLEEP_SECONDS = 10

def load_spec(spec_path):
    if not os.path.isfile(spec_path):
        print(f"❌ Spec file not found at {spec_path}")
        sys.exit(1)
    with open(spec_path) as f:
        return json.load(f)

def get_latest_zip_file(zip_dir):
    if not os.path.isdir(zip_dir):
        print(f"❌ Directory not found: {zip_dir}")
        sys.exit(1)
    zip_files = [f for f in os.listdir(zip_dir) if f.endswith(".zip")]
    if not zip_files:
        print(f"❌ No ZIP files found in {zip_dir}")
        sys.exit(1)
    zip_files.sort(key=lambda x: os.path.getmtime(os.path.join(zip_dir, x)), reverse=True)
    return os.path.join(zip_dir, zip_files[0])

def ensure_bot_exists(bot_name, bot, env, region):
    client = boto3.client("lexv2-models", region_name=region)
    bots = client.list_bots()['botSummaries']
    existing_bot = next((b for b in bots if b['botName'] == bot_name), None)
    if existing_bot:
        print(f"✅ Bot '{bot_name}' already exists.")
        return

    print(f"🛠 Bot '{bot_name}' not found — invoking build_bot.py...")
    subprocess.run([
        sys.executable, "deploy/create_new_lex_bot.py", "--bot", bot, "--env", env
    ], check=True)
    print("✅ Bot creation complete.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", required=True, help="Bot name (directory)")
    parser.add_argument("--env", required=True, help="Environment (e.g., dev, qa)")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    zip_dir = ZIP_DIR_TEMPLATE.format(bot=args.bot, env=args.env)
    zip_file = get_latest_zip_file(zip_dir)
    config_path = CONFIG_FILE_TEMPLATE.format(bot=args.bot)

    if not os.path.exists(config_path):
        sys.exit(f"❌ Config file not found: {config_path}")

    with open(config_path) as f:
        lex_config = json.load(f)

    env_config = lex_config.get(args.env)
    if not env_config:
        sys.exit(f"❌ Environment '{args.env}' not found in config")

    bot_name = env_config["bot_name"]

    print(f"📦 Importing bot from ZIP: {zip_file}")
    ensure_bot_exists(bot_name, args.bot, args.env, args.region)
    client = boto3.client("lexv2-models", region_name=args.region)

    print("⏫ Requesting upload URL...")
    upload_response = client.create_upload_url()
    upload_url = upload_response["uploadUrl"]
    upload_id = upload_response["importId"]

    print(f"📤 Uploading ZIP to Lex using UploadId: {upload_id}")
    with open(zip_file, "rb") as f:
        resp = requests.put(upload_url, data=f.read())
        if resp.status_code != 200:
            print(f"❌ Failed to upload ZIP: {resp.status_code}")
            sys.exit(1)

    botImportSpecs = {
        "botImportSpecification": {
            "botName": env_config["bot_name"],
            "roleArn": env_config["lex_role_arn"],
            "dataPrivacy": {
                "childDirected": env_config.get("child_directed", False)
            }
        }
    }

    print(f"🚀 Starting import with UploadId: {upload_id}")
    import_response = client.start_import(
        importId=upload_id,
        resourceSpecification=botImportSpecs,
        mergeStrategy='Overwrite'  # Capital O required by AWS
    )

    import_id = import_response["importId"]
    print(f"🆔 Import started with ID: {import_id}")

    status = "InProgress"
    attempts = 0

    while status in ["InProgress", "Waiting"] and attempts < MAX_ATTEMPTS:
        time.sleep(SLEEP_SECONDS)
        result = client.describe_import(importId=import_id)
        status = result["importStatus"]
        print(f"⏳ Import status: {status}")

        if status == "Completed":
            print("✅ Import completed successfully.")
            return
        elif status == "Failed":
            print("❌ Import failed.")
            print(json.dumps(result, indent=2))
            sys.exit(1)

        attempts += 1

    print("❌ Timed out waiting for import to complete.")
    sys.exit(1)

if __name__ == "__main__":
    main()
