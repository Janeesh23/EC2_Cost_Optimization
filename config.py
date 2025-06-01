import os

EBS_VOLUME_AGE_DAYS = int(os.environ.get("EBS_VOLUME_AGE_DAYS", "7"))
SNAPSHOT_RETENTION_DAYS = int(os.environ.get("SNAPSHOT_RETENTION_DAYS", "30"))
AMI_RETENTION_DAYS = int(os.environ.get("AMI_RETENTION_DAYS", "60"))
IDLE_CPU_THRESHOLD = float(os.environ.get("IDLE_CPU_THRESHOLD", "5.0"))
IDLE_IO_THRESHOLD_MB = float(os.environ.get("IDLE_IO_THRESHOLD_MB", "1.0"))
LOG_S3_BUCKET = os.environ.get("LOG_S3_BUCKET", "ec2-cost-logs")
LB_MIN_AGE_MINUTES = int(os.environ.get("LB_MIN_AGE_MINUTES", "60"))
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
