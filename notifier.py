import boto3
import os
import logging
from collections import Counter
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

def notify_cleanup_changes(log_entries):

    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not configured. Skipping notification.")
        return


    deleted_or_released = [log for log in log_entries if log.get("action") in {"deleted", "released"}]
    notify_only = [log for log in log_entries if log.get("action") == "notify"]

    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()


    if deleted_or_released:
        type_counts = Counter(log["resource_type"] for log in deleted_or_released)
        summary_lines = [f"{count} {rtype}(s)" for rtype, count in type_counts.items()]
        message = "AWS EC2 Cleanup Summary:\n\n" + "\n".join(summary_lines)
        message += f"\n\nTimestamp: {timestamp} UTC"

        try:
            sns = boto3.client("sns")
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="EC2 Cost Optimization Cleanup Summary",
                Message=message
            )
            logger.info("Cleanup summary notification sent via SNS.")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to send cleanup SNS notification: {str(e)}")


    if notify_only:
        lines = []
        for log in notify_only:
            rid = log.get("resource_id", "unknown")
            reason = log.get("reason", "No reason provided")
            lines.append(f"{log['resource_type']} {rid} - {reason}")
        message = "AWS EC2 Cost Alert:\n\n" + "\n".join(lines)
        message += f"\n\nTimestamp: {timestamp} UTC"

        try:
            sns = boto3.client("sns")
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="EC2 Idle Resource Notification",
                Message=message
            )
            logger.info("Notify-only alert sent via SNS.")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to send notify-only SNS alert: {str(e)}")
