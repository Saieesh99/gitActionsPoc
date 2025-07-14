# deploy_s3_bucket.py

import boto3
import botocore
import os

def create_s3_bucket(bucket_name, region=None):
    s3 = boto3.client("s3", region_name=region)

    try:
        if region == "us-east-1":
            response = s3.create_bucket(Bucket=bucket_name)
        else:
            location = {'LocationConstraint': region}
            response = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)

        print(f"✅ S3 Bucket created: {bucket_name}")
        return response

    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "BucketAlreadyOwnedByYou":
            print(f"⚠️ Bucket '{bucket_name}' already exists and is owned by you.")
        else:
            raise

if __name__ == "__main__":
    # You can also get these via environment variables
    BUCKET_NAME = os.getenv("BUCKET_NAME", "my-voicemail-bucket")
    REGION = os.getenv("AWS_REGION", "ap-south-1")  # change as needed

    create_s3_bucket(bucket_name=BUCKET_NAME, region=REGION)
