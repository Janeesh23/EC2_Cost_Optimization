import boto3
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError
from config import SNAPSHOT_RETENTION_DAYS

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def cleanup_old_snapshots():
    
    ec2 = boto3.client("ec2")
    deleted_snapshots = []

    try:
        snapshot_response = ec2.describe_snapshots(OwnerIds=["self"])
        snapshots = snapshot_response.get("Snapshots", [])

        for snapshot in snapshots:
            snapshot_id = snapshot.get("SnapshotId")
            volume_id = snapshot.get("VolumeId")
            start_time = snapshot.get("StartTime")

            if not snapshot_id or not start_time:
                logger.warning(f"Skipping snapshot with missing ID or time.")
                continue

            age_days = (datetime.now(timezone.utc) - start_time).days

            if age_days >= SNAPSHOT_RETENTION_DAYS:
                if not volume_id:
                   
                    try:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        logger.info(f"Deleted snapshot {snapshot_id}: no volume attached, age {age_days} days")
                        deleted_snapshots.append({
                            "resource_id": snapshot_id,
                            "action": "deleted",
                            "resource_type": "EBS Snapshot",
                            "reason": f"Not linked to any volume, age {age_days} days",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except ClientError as e:
                        logger.error(f"Failed to delete snapshot {snapshot_id}: {str(e)}")
                    continue

                
                try:
                    volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                    volume = volume_response['Volumes'][0]
                    attachments = volume.get("Attachments", [])

                    if not attachments:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        logger.info(f"Deleted snapshot {snapshot_id}: linked volume is detached, age {age_days} days")
                        deleted_snapshots.append({
                            "resource_id": snapshot_id,
                            "action": "deleted",
                            "resource_type": "EBS Snapshot",
                            "reason": f"Volume not attached to any instance, age {age_days} days",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        logger.info(f"Skipping snapshot {snapshot_id}: volume attached")

                except ec2.exceptions.ClientError as e:
                    if e.response["Error"]["Code"] == "InvalidVolume.NotFound":
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        logger.info(f"Deleted snapshot {snapshot_id}: volume missing, age {age_days} days")
                        deleted_snapshots.append({
                            "resource_id": snapshot_id,
                            "action": "deleted",
                            "resource_type": "EBS Snapshot",
                            "reason": f"Linked volume not found (possibly deleted), age {age_days} days",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        logger.error(f"Error describing volume {volume_id}: {str(e)}")

            else:
                logger.info(f"Skipping snapshot {snapshot_id}: only {age_days} days old")

    except (ClientError, BotoCoreError) as err:
        logger.error(f"Failed to describe snapshots: {str(err)}")

    return deleted_snapshots
