import boto3
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError
from config import AMI_RETENTION_DAYS

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def cleanup_old_amis():
    """Deregisters AMIs older than the configured threshold and deletes associated snapshots."""
    ec2 = boto3.client("ec2")
    cleaned_amis = []

    try:
        # Step 1: List all AMIs owned by the account
        image_response = ec2.describe_images(Owners=["self"])
        images = image_response.get("Images", [])

        for image in images:
            image_id = image.get("ImageId")
            creation_date_str = image.get("CreationDate")
            name = image.get("Name", "Unnamed")

            if not image_id or not creation_date_str:
                logger.warning("AMI missing ID or CreationDate. Skipping.")
                continue

            # Convert creation date to datetime
            creation_date = datetime.strptime(creation_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - creation_date).days

            if age_days >= AMI_RETENTION_DAYS:
                try:
                    # Step 2: Deregister the AMI
                    ec2.deregister_image(ImageId=image_id)
                    logger.info(f"Deregistered AMI {image_id} (Name: {name}, Age: {age_days} days)")

                    cleaned_amis.append({
                        "resource_id": image_id,
                        "action": "deleted",
                        "resource_type": "AMI",
                        "reason": f"Older than {AMI_RETENTION_DAYS} days",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    # Step 3: Delete associated snapshots
                    for mapping in image.get("BlockDeviceMappings", []):
                        ebs = mapping.get("Ebs")
                        if ebs and "SnapshotId" in ebs:
                            snapshot_id = ebs["SnapshotId"]
                            try:
                                ec2.delete_snapshot(SnapshotId=snapshot_id)
                                logger.info(f"Deleted snapshot {snapshot_id} from AMI {image_id}")

                                cleaned_amis.append({
                                    "resource_id": snapshot_id,
                                    "action": "deleted",
                                    "resource_type": "EBS Snapshot",
                                    "reason": f"Snapshot associated with deregistered AMI {image_id}",
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            except ClientError as snap_error:
                                logger.error(f"Failed to delete snapshot {snapshot_id}: {str(snap_error)}")

                except ClientError as e:
                    logger.error(f"Failed to deregister AMI {image_id}: {str(e)}")
            else:
                logger.info(f"Skipping AMI {image_id}: age {age_days} days")

    except (ClientError, BotoCoreError) as e:
        logger.error(f"Error describing AMIs: {str(e)}")

    return cleaned_amis
