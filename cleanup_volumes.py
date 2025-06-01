import boto3
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError
from config import EBS_VOLUME_AGE_DAYS

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def cleanup_unattached_volumes():
    
    ec2 = boto3.client("ec2")
    deleted_volumes = []

    try:
        response = ec2.describe_volumes()
        volumes = response.get("Volumes", [])

        for volume in volumes:
            volume_id = volume.get("VolumeId")
            state = volume.get("State")
            create_time = volume.get("CreateTime")

            if state == "available":
               
                age_days = (datetime.now(timezone.utc) - create_time).days

                if age_days >= EBS_VOLUME_AGE_DAYS:
                    try:
                        ec2.delete_volume(VolumeId=volume_id)
                        logger.info(f"Deleted volume {volume_id} (age: {age_days} days)")

                        deleted_volumes.append({
                            "resource_id": volume_id,
                            "action": "deleted",
                            "resource_type": "EBS Volume",
                            "reason": f"Unattached and older than {EBS_VOLUME_AGE_DAYS} days",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except ClientError as e:
                        logger.error(f"Failed to delete volume {volume_id}: {str(e)}")
            else:
                logger.info(f"Skipping volume {volume_id}: state is {state}")

    except (ClientError, BotoCoreError) as e:
        logger.error(f"Error describing volumes: {str(e)}")

    return deleted_volumes
