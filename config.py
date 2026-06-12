import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("aws_access_key_id")
AWS_SECRET_KEY = os.getenv("aws_secret_access_key")
AWS_SESSION_TOKEN = os.getenv("aws_session_token")
S3_RAW_BUCKET = os.getenv("S3_RAW_BUCKET")
S3_COG_BUCKET = os.getenv("S3_COG_BUCKET")
S3_PREVIEW_BUCKET = os.getenv("S3_PREVIEW_BUCKET")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

GEOSERVER_URL = os.getenv("GEOSERVER_URL")
GEOSERVER_USER = os.getenv("GEOSERVER_USER")
GEOSERVER_PASSWORD = os.getenv("GEOSERVER_PASSWORD")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")