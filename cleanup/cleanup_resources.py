import boto3
import json
import sys
import subprocess
from botocore.exceptions import ClientError

# ===== Terraform Helper =====
def terraform_state_rm(resource_address):
    try:
        result = subprocess.run(
            ["terraform", "state", "rm", resource_address],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Removed from Terraform state: {resource_address}")
    except subprocess.CalledProcessError as e:
        print(f"Terraform state rm failed: {resource_address}\n{e.stderr}")

# ===== IAM Role =====
def delete_iam_role(role_name):
    iam = boto3.client('iam')
    try:
        attached = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        for policy in attached:
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
        inline_policies = iam.list_role_policies(RoleName=role_name)['PolicyNames']
        for policy_name in inline_policies:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        iam.delete_role(RoleName=role_name)
        print(f"IAM role deleted: {role_name}")
    except ClientError as e:
        print(f"Error deleting IAM role {role_name}: {e}")

# ===== IAM Policy =====
def delete_iam_policy(policy_name):
    iam = boto3.client('iam')
    try:
        policies = iam.list_policies(Scope='Local')['Policies']
        for p in policies:
            if p['PolicyName'] == policy_name:
                versions = iam.list_policy_versions(PolicyArn=p['Arn'])['Versions']
                for v in versions:
                    if not v['IsDefaultVersion']:
                        iam.delete_policy_version(PolicyArn=p['Arn'], VersionId=v['VersionId'])
                iam.delete_policy(PolicyArn=p['Arn'])
                print(f"IAM policy deleted: {policy_name}")
                return
        print(f"IAM policy not found: {policy_name}")
    except ClientError as e:
        print(f"Error deleting IAM policy {policy_name}: {e}")

# ===== Lambda =====
def delete_lambda_function(function_name):
    lambda_client = boto3.client('lambda')
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print(f"Lambda deleted: {function_name}")
    except ClientError as e:
        print(f"Error deleting Lambda {function_name}: {e}")

# ===== S3 Bucket =====
def delete_s3_bucket(bucket_name):
    s3 = boto3.resource('s3')
    try:
        bucket = s3.Bucket(bucket_name)
        bucket.objects.all().delete()
        bucket.object_versions.all().delete()
        bucket.delete()
        print(f"S3 bucket deleted: {bucket_name}")
    except ClientError as e:
        print(f"Error deleting S3 bucket {bucket_name}: {e}")

# ===== EventBridge Rule =====
def delete_eventbridge_rule(rule_name):
    events = boto3.client('events')
    try:
        targets = events.list_targets_by_rule(Rule=rule_name)['Targets']
        if targets:
            target_ids = [t['Id'] for t in targets]
            events.remove_targets(Rule=rule_name, Ids=target_ids)
        events.delete_rule(Name=rule_name)
        print(f"EventBridge rule deleted: {rule_name}")
    except ClientError as e:
        print(f"Error deleting EventBridge rule {rule_name}: {e}")


def get_all_bots():
    lex = boto3.client('lexv2-models')
    all_bots = []

    next_token = None
    while True:
        if next_token:
            response = lex.list_bots(nextToken=next_token, maxResults=50)
        else:
            response = lex.list_bots(maxResults=50)

        bots = response.get('botSummaries', [])
        all_bots.extend(bots)

        next_token = response.get('nextToken')
        if not next_token:
            break

    return all_bots

# ===== Lex Bot =====
def delete_lex_bot(bot_name):
    lex = boto3.client('lexv2-models')
    
    try:
        bots = get_all_bots()
        print(f"Total bots found: {len(bots)}")

        # print("bots ",bots)
        for bot in bots:
            if bot['botName'] == bot_name:
                lex.delete_bot(botId=bot['botId'], skipResourceInUseCheck=True)
                print(f"Lex bot deleted: {bot_name}")
                return
        print(f"Lex bot not found: {bot_name}")
    except ClientError as e:
        print(f"Error deleting Lex bot {bot_name}: {e}")

# ===== Cleanup Runner =====
def cleanup_resources(config_file, env):
    with open(config_file) as f:
        config = json.load(f)

    if env not in config:
        print(f"Environment '{env}' not found in config.")
        return

    resources = config[env]

    # IAM Roles
    for item in resources.get("iam_roles", []):
        name = item["name"] if isinstance(item, dict) else item
        tf = item.get("tf") if isinstance(item, dict) else None
        delete_iam_role(name)
        if tf:
            terraform_state_rm(tf)

    # IAM Policies
    for item in resources.get("iam_policies", []):
        name = item["name"] if isinstance(item, dict) else item
        tf = item.get("tf") if isinstance(item, dict) else None
        delete_iam_policy(name)
        if tf:
            terraform_state_rm(tf)

    # S3 Buckets
    for item in resources.get("s3_buckets", []):
        name = item["name"] if isinstance(item, dict) else item
        tf = item.get("tf") if isinstance(item, dict) else None
        delete_s3_bucket(name)
        if tf:
            terraform_state_rm(tf)

    # Lambda Functions
    for item in resources.get("lambda_functions", []):
        name = item["name"] if isinstance(item, dict) else item
        delete_lambda_function(name)

    # EventBridge Rules
    for item in resources.get("eventbridge_rules", []):
        name = item["name"] if isinstance(item, dict) else item
        delete_eventbridge_rule(name)

    # Lex Bots
    for item in resources.get("lex_bots", []):
        name = item["name"] if isinstance(item, dict) else item
        delete_lex_bot(name)

# ===== Entry Point =====
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python cleanup_resources.py <config_file> <environment>")
        sys.exit(1)
    config_path = sys.argv[1]
    environment = sys.argv[2]
    cleanup_resources(config_path, environment)
