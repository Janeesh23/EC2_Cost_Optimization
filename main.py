import logging
from cleanup_volumes import cleanup_unattached_volumes
from cleanup_snapshots import cleanup_old_snapshots
from cleanup_instances import cleanup_idle_instances
from cleanup_elastic_ips import cleanup_unattached_elastic_ips
from cleanup_load_balancers import cleanup_unused_load_balancers
from cleanup_amis import cleanup_old_amis
from logger import upload_log_to_s3
from notifier import notify_cleanup_changes  # NEW

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main Lambda handler to orchestrate all EC2 cleanup tasks and log results to S3/SNS."""
    all_logs = []

    # Cleanup unattached EBS Volumes
    try:
        volume_logs = cleanup_unattached_volumes()
        all_logs.extend(volume_logs)
    except Exception as e:
        logger.error(f"Error during EBS volume cleanup: {str(e)}")

    # Cleanup old EBS Snapshots
    try:
        snapshot_logs = cleanup_old_snapshots()
        all_logs.extend(snapshot_logs)
    except Exception as e:
        logger.error(f"Error during snapshot cleanup: {str(e)}")

    # Notify on idle EC2 Instances
    try:
        instance_logs = cleanup_idle_instances()
        all_logs.extend(instance_logs)
    except Exception as e:
        logger.error(f"Error during idle instance check: {str(e)}")

    # Release unattached Elastic IPs
    try:
        eip_logs = cleanup_unattached_elastic_ips()
        all_logs.extend(eip_logs)
    except Exception as e:
        logger.error(f"Error during Elastic IP release: {str(e)}")

    # Delete unused Load Balancers
    try:
        lb_logs = cleanup_unused_load_balancers()
        all_logs.extend(lb_logs)
    except Exception as e:
        logger.error(f"Error during load balancer cleanup: {str(e)}")

    # Cleanup old AMIs and associated snapshots
    try:
        ami_logs = cleanup_old_amis()
        all_logs.extend(ami_logs)
    except Exception as e:
        logger.error(f"Error during AMI cleanup: {str(e)}")

    # Upload final log summary to S3
    try:
        upload_log_to_s3(all_logs)
    except Exception as e:
        logger.error(f"Error uploading logs to S3: {str(e)}")

    # Notify SNS about deleted/released resources
    try:
        notify_cleanup_changes(all_logs)
    except Exception as e:
        logger.error(f"Error sending SNS notifications: {str(e)}")
