import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def cleanup_unattached_elastic_ips():

    ec2 = boto3.client("ec2")
    released_ips = []

    try:

        response = ec2.describe_addresses()
        addresses = response.get("Addresses", [])

        for address in addresses:
            allocation_id = address.get("AllocationId")
            public_ip = address.get("PublicIp")
            instance_id = address.get("InstanceId")
            network_interface_id = address.get("NetworkInterfaceId")


            if not instance_id and not network_interface_id:
                try:
                    ec2.release_address(AllocationId=allocation_id)
                    logger.info(f"Released Elastic IP {public_ip} (AllocationId: {allocation_id})")

                    released_ips.append({
                        "resource_id": allocation_id,
                        "action": "released",
                        "resource_type": "Elastic IP",
                        "reason": "Unattached Elastic IP consuming cost",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except ClientError as e:
                    logger.error(f"Failed to release Elastic IP {public_ip}: {str(e)}")
            else:
                logger.info(f"Skipping Elastic IP {public_ip}: still in use")

    except (ClientError, BotoCoreError) as e:
        logger.error(f"Error describing Elastic IPs: {str(e)}")

    return released_ips
