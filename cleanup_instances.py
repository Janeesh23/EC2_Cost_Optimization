import boto3
import logging
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError, BotoCoreError
from config import IDLE_CPU_THRESHOLD

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def cleanup_idle_instances():
    """Identifies EC2 instances with low CPU usage and logs for notification."""
    ec2 = boto3.client("ec2")
    cloudwatch = boto3.client("cloudwatch")
    idle_instances = []

    try:
        # Step 1: Get all running EC2 instances
        reservations = ec2.describe_instances(Filters=[
            {"Name": "instance-state-name", "Values": ["running"]}
        ]).get("Reservations", [])

        instances = [inst for r in reservations for inst in r.get("Instances", [])]

        for instance in instances:
            instance_id = instance.get("InstanceId")
            launch_time = instance.get("LaunchTime")

            if not instance_id or not launch_time:
                logger.warning("Instance missing ID or launch time. Skipping.")
                continue

            # Step 2: Define time range (last 7 days)
            end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            start_time = end_time - timedelta(days=7)

            try:
                # Step 3: Get average CPU utilization
                cpu_response = cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=["Average"]
                )

                cpu_datapoints = cpu_response.get("Datapoints", [])
                avg_cpu = sum(dp["Average"] for dp in cpu_datapoints) / len(cpu_datapoints) if cpu_datapoints else 0

                # Step 4: Check if CPU is below or equal to threshold
                if avg_cpu <= IDLE_CPU_THRESHOLD:
                    logger.info(f"Instance {instance_id} is idle: CPU={avg_cpu:.2f}%")

                    idle_instances.append({
                        "resource_id": instance_id,
                        "action": "notify",
                        "resource_type": "EC2 Instance",
                        "reason": f"Idle: CPU <= {IDLE_CPU_THRESHOLD}% over 7 days",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except (ClientError, BotoCoreError) as metric_error:
                logger.error(f"Error fetching metrics for {instance_id}: {str(metric_error)}")

    except (ClientError, BotoCoreError) as ec2_error:
        logger.error(f"Error describing instances: {str(ec2_error)}")

    return idle_instances
