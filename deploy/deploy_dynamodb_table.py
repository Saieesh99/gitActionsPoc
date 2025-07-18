import boto3
import os
import sys
from botocore.exceptions import ClientError

def create_table(dynamodb=None, table_name=None):
    try:
        if not dynamodb:
            dynamodb = boto3.resource('dynamodb')

        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'flowid', 'KeyType': 'HASH'},  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'flowid', 'AttributeType': 'S'},
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        table.wait_until_exists()
        print(f"✅ Table '{table_name}' created successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️ Table '{table_name}' already exists.")
        else:
            print(f"❌ Failed to create table: {e}")
            sys.exit(1)

def main():
    # Get environment (dev, uat, qa, prod) from environment variables
    env = os.getenv('ENV', 'dev').lower()
    valid_envs = ['dev', 'uat', 'qa', 'prod']

    if env not in valid_envs:
        print(f"❌ Invalid environment '{env}'. Must be one of {valid_envs}")
        sys.exit(1)

    table_name = f"flow-tracking-{env}"

    print(f"Creating table for environment: {env}")
    create_table(table_name=table_name)

if __name__ == '__main__':
    main()



# ENV=${{ github.event.inputs.env }} python create_dynamodb_table.py