import boto3
import os
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY

# Read the single bucket name from environment
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "satleo-satellite-data")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

from botocore.config import Config

s3_client = boto3.client(
    "s3",
    region_name="ap-south-2",
    endpoint_url="https://s3.ap-south-2.amazonaws.com",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    config=Config(signature_version='s3v4')
)

def upload_to_raw_bucket(local_path: str, s3_key: str) -> str:
    # Prefix with the folder from the image
    full_key = f"raw-satellite-data/{s3_key}"
    s3_client.upload_file(local_path, S3_BUCKET_NAME, full_key)
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET_NAME, 'Key': full_key},
        ExpiresIn=43200  # 12 hours
    )
    return presigned_url

def upload_cog_to_s3(local_cog_path: str, dataset_id: str) -> str:
    # Prefix with the folder from the image
    full_key = f"cog data/{dataset_id}.tif"
    s3_client.upload_file(local_cog_path, S3_BUCKET_NAME, full_key)
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET_NAME, 'Key': full_key},
        ExpiresIn=43200  # 12 hours
    )
    return presigned_url