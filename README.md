#  EC2 Cost Optimization Lambda

An automated AWS Lambda solution that performs cost-saving cleanups on unused or idle EC2-related resources such as:

-  Unattached EBS volumes  
-  Old EBS snapshots  
-  Idle EC2 instances  
-  Unused Elastic IPs  
-  Unused Load Balancers  
-  Old AMIs and their snapshots  

The Lambda function is triggered daily via **Amazon EventBridge (cron)**, and logs cleanup results to **Amazon S3** and sends **SNS notifications**.

---

## Features

- **EBS Volume Cleanup**: Deletes unattached volumes older than a configurable threshold.  
- **EBS Snapshot Cleanup**: Deletes snapshots not attached to in-use volumes or volumes that no longer exist.  
- **Idle EC2 Notification**: Identifies running instances with low CPU usage for 7 days.  
- **Elastic IP Release**: Releases unassociated Elastic IPs to avoid unnecessary billing.  
- **Load Balancer Cleanup**: Deletes ALBs/NLBs with no registered targets.  
- **AMI Cleanup**: Deregisters old AMIs and deletes their associated snapshots.  
- **S3 Logging**: Uploads structured JSON logs to a designated S3 bucket.  
- **SNS Alerts**: Sends cleanup and idle instance notifications via SNS.  

---

## EventBridge Schedule (Cron)

EventBridge triggers the Lambda function at a fixed interval (e.g., once daily):

```text
cron(0 2 * * ? *)  # Every day at 2:00 AM UTC
```

> Configure via AWS Console.

---

## IAM Permissions Required

Attach this **inline policy** to the IAM Role assigned to the Lambda:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeImages", "ec2:DescribeInstances", "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots", "ec2:DeleteSnapshot", "ec2:DeleteVolume",
        "ec2:ReleaseAddress", "ec2:DeregisterImage", "ec2:DescribeAddresses",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:DeleteLoadBalancer",
        "cloudwatch:GetMetricStatistics",
        "sns:Publish"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Environment Variables

| Variable Name         | Description                                              | Default Value      |
|-----------------------|----------------------------------------------------------|--------------------|
| `EBS_VOLUME_AGE_DAYS` | Max age of unattached volumes to keep (in days)          | 7                  |
| `SNAPSHOT_RETENTION_DAYS` | Max age of snapshots to retain (in days)              | 30                 |
| `AMI_RETENTION_DAYS`  | Max age of AMIs to keep (in days)                        | 60                 |
| `IDLE_CPU_THRESHOLD`  | CPU % threshold to detect idle EC2 instances             | 5.0                |
| `LB_MIN_AGE_MINUTES`  | Minimum age for load balancers to be considered (in min) | 60                 |
| `LOG_S3_BUCKET`       | Target S3 bucket for uploading logs                      | `ec2-cost-logs`    |
| `SNS_TOPIC_ARN`       | SNS topic ARN for notifications                          | *(required)*       |

---

## Deployment

1. Package Lambda with all Python files  
2. Zip and Upload via AWS Console.
3. Attach IAM Role with the inline policy shown above.
4. Create EventBridge Rule with desired cron expression.
5. Set environment variables in the Lambda configuration.

---

## Log Structure (S3 JSON)

Each JSON log entry uploaded to S3 looks like:

```json
{
  "resource_id": "vol-123456",
  "action": "deleted",
  "resource_type": "EBS Volume",
  "reason": "Unattached and older than 7 days",
  "timestamp": "2025-06-01T10:05:23Z"
}
```

---

## SNS Notifications

### Topic 1: Cleanup Summary  
- **Subject**: `EC2 Cost Optimization Cleanup Summary`  
- **Details**: Lists number of deleted volumes, snapshots, AMIs, etc.

### Topic 2: Idle Instance Alerts  
- **Subject**: `EC2 Idle Resource Notification`  
- **Details**: Lists EC2 instances with consistently low CPU usage.

---

