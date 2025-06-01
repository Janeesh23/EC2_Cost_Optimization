import logging
from cleanup_volumes import cleanup_unattached_volumes
from cleanup_snapshots import cleanup_old_snapshots
from cleanup_instances import cleanup_idle_instances
from cleanup_elastic_ips import cleanup_unattached_elastic_ips
from cleanup_load_balancers import cleanup_unused_load_balancers
from cleanup_amis import cleanup_old_amis
from logger import upload_log_to_s3
from notifier import notify_cleanup_changes  

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    all_logs = []


    try:
        volume_logs = cleanup_unattached_volumes()
        all_logs.extend(volume_logs)
    except Exception as e:
        logger.error(f"Error during EBS volume cleanup: {str(e)}")

 
    try:
        snapshot_logs = cleanup_old_snapshots()
        all_logs.extend(snapshot_logs)
    except Exception as e:
        logger.error(f"Error during snapshot cleanup: {str(e)}")


    try:
        instance_logs = cleanup_idle_instances()
        all_logs.extend(instance_logs)
    except Exception as e:
        logger.error(f"Error during idle instance check: {str(e)}")


    try:
        eip_logs = cleanup_unattached_elastic_ips()
        all_logs.extend(eip_logs)
    except Exception as e:
        logger.error(f"Error during Elastic IP release: {str(e)}")


    try:
        lb_logs = cleanup_unused_load_balancers()
        all_logs.extend(lb_logs)
    except Exception as e:
        logger.error(f"Error during load balancer cleanup: {str(e)}")


    try:
        ami_logs = cleanup_old_amis()
        all_logs.extend(ami_logs)
    except Exception as e:
        logger.error(f"Error during AMI cleanup: {str(e)}")


    try:
        upload_log_to_s3(all_logs)
    except Exception as e:
        logger.error(f"Error uploading logs to S3: {str(e)}")


    try:
        notify_cleanup_changes(all_logs)
    except Exception as e:
        logger.error(f"Error sending SNS notifications: {str(e)}")
