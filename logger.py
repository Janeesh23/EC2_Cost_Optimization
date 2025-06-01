import json
import boto3
import logging
from datetime import datetime
from botocore.exceptions import BotoCoreError, ClientError
from config import LOG_S3_BUCKET

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def upload_log_to_s3(log_entries):
    """Uploads structured JSON logs to the specified S3 bucket."""
    s3 = boto3.client("s3")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    filename = f"{timestamp}-summary.json"

    try:
        log_data = json.dumps(log_entries, indent=2)
        s3.put_object(Bucket=LOG_S3_BUCKET, Key=filename, Body=log_data)
        logger.info(f"Successfully uploaded log to S3 bucket {LOG_S3_BUCKET} as {filename}")
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to upload logs to S3: {str(e)}")
