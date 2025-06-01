import boto3
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError
from config import LB_MIN_AGE_MINUTES

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def cleanup_unused_load_balancers():
    """Deletes ALBs/NLBs with no registered targets in any target group and older than threshold."""
    elb = boto3.client("elbv2")
    deleted_lbs = []

    try:
        # Step 1: Describe all load balancers
        lb_response = elb.describe_load_balancers()
        load_balancers = lb_response.get("LoadBalancers", [])

        for lb in load_balancers:
            lb_arn = lb.get("LoadBalancerArn")
            lb_name = lb.get("LoadBalancerName")
            created_time = lb.get("CreatedTime")

            if not lb_arn or not lb_name or not created_time:
                logger.warning("Load balancer missing ARN, Name, or CreatedTime. Skipping.")
                continue

            age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60

            try:
                # Step 2: Get target groups for this load balancer
                tg_response = elb.describe_target_groups(LoadBalancerArn=lb_arn)
                target_groups = tg_response.get("TargetGroups", [])

                has_registered_targets = False

                # Step 3: Check each target group for targets
                for tg in target_groups:
                    tg_arn = tg.get("TargetGroupArn")
                    if not tg_arn:
                        continue

                    th_response = elb.describe_target_health(TargetGroupArn=tg_arn)
                    targets = th_response.get("TargetHealthDescriptions", [])

                    if targets:
                        has_registered_targets = True
                        break

                # Step 4: If no targets and older than threshold, proceed to delete
                if not has_registered_targets and age_minutes >= LB_MIN_AGE_MINUTES:
                    # Step 4.1: Delete all listeners first
                    try:
                        listeners_response = elb.describe_listeners(LoadBalancerArn=lb_arn)
                        listeners = listeners_response.get("Listeners", [])
                        for listener in listeners:
                            listener_arn = listener["ListenerArn"]
                            elb.delete_listener(ListenerArn=listener_arn)
                            logger.info(f"Deleted listener {listener_arn} from LB {lb_name}")
                    except Exception as listener_error:
                        logger.error(f"Failed to delete listeners for {lb_name}: {str(listener_error)}")

                    # Step 4.2: Delete the load balancer
                    elb.delete_load_balancer(LoadBalancerArn=lb_arn)
                    logger.info(f"Deleted load balancer {lb_name} (ARN: {lb_arn})")

                    deleted_lbs.append({
                        "resource_id": lb_arn,
                        "action": "deleted",
                        "resource_type": "Load Balancer",
                        "reason": f"No registered targets and older than {LB_MIN_AGE_MINUTES} minutes",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    logger.info(f"Skipping load balancer {lb_name}: either has targets or is too new")

            except (ClientError, BotoCoreError) as inner_error:
                logger.error(f"Failed checking/deleting load balancer {lb_name}: {str(inner_error)}")

    except (ClientError, BotoCoreError) as outer_error:
        logger.error(f"Error describing load balancers: {str(outer_error)}")

    return deleted_lbs
