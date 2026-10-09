"""
CloudSnack - Cryptic AWS Error Translator
Translates intimidating AWS error messages into plain English,
reassuring empathy, and safe copy-paste fixes.
"""

import re
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class ErrorTranslation:
    raw_error: str
    category: str
    what_aws_said: str
    what_it_actually_means: str
    empathy_note: str
    quick_fix_cli: str
    preventative_tip: str


# Knowledge base of frequent scary AWS errors
ERROR_KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "pattern": r"(InvalidParameterCombination|AllocatedStorage.*StorageType)",
        "category": "RDS Database",
        "title": "RDS Storage Parameter Mismatch",
        "what_it_actually_means": "You asked AWS to create an RDS database with storage settings that contradict each other (e.g. asking for gp3 with IOPS lower than 3000 or below the minimum volume size for that engine).",
        "empathy_note": "Don't sweat it. AWS parameter combinations have more fine print than a loan agreement. Every senior engineer has wrestled with this exact error.",
        "quick_fix_cli": "# Set allocated storage to at least 20GB and default gp3 baseline:\naws rds create-db-instance \\\n  --db-instance-identifier my-db \\\n  --db-instance-class db.t4g.micro \\\n  --engine postgres \\\n  --allocated-storage 20 \\\n  --storage-type gp3",
        "preventative_tip": "For dev testing, always stick to 20GB gp3 with default baseline IOPS (3000) so you don't trigger pricing or ratio limits.",
    },
    {
        "pattern": r"(ResourceInUseException|The vpc '.*' has dependencies and cannot be deleted|DependencyViolation)",
        "category": "VPC & Networking",
        "title": "VPC Has Hidden Dependencies",
        "what_it_actually_means": "AWS refused to delete this VPC because there are still hidden ghost resources living inside it (like an old Elastic Network Interface, NAT Gateway, Internet Gateway, or Security Group).",
        "empathy_note": "AWS VPC deletion is infamous! Deleting a VPC without finding all 6 hidden child resources is like solving a locked-room mystery. You're not crazy; the error message is just unhelpful.",
        "quick_fix_cli": "# List the stubborn network interfaces locking the VPC:\naws ec2 describe-network-interfaces \\\n  --filters Name=vpc-id,Values=<YOUR_VPC_ID> \\\n  --query 'NetworkInterfaces[*].[NetworkInterfaceId,Description,Status]' --output table\n\n# Detach and delete any non-default ENIs, then delete the VPC.",
        "preventative_tip": "If you use Terraform or AWS CDK to create VPCs, destroy them with the same tool instead of manual console clicking to let dependency graphs clean up automatically.",
    },
    {
        "pattern": r"(UnauthorizedOperation|AccessDenied|is not authorized to perform)",
        "category": "IAM & Permissions",
        "title": "IAM Permission Wall",
        "what_it_actually_means": "Your IAM user or role is missing an explicit 'Allow' for this specific API action, OR a Service Control Policy (SCP) / Permission Boundary is politely shutting the door.",
        "empathy_note": "Welcome to the AWS rite of passage. 99% of developers hit IAM walls weekly. It doesn't mean your code is broken—it just means IAM is doing its bodyguard job a little too zealously.",
        "quick_fix_cli": "# Check your current caller identity to see who AWS thinks you are:\naws sts get-caller-identity\n\n# If using an assumed role, check attached policies:\naws iam list-attached-role-policies --role-name <YOUR_ROLE_NAME>",
        "preventative_tip": "Use the AWS Policy Simulator in the console to test actions without trial-and-error deployments.",
    },
    {
        "pattern": r"(BucketNotEmpty|The bucket you tried to delete is not empty)",
        "category": "S3 Storage",
        "title": "S3 Refuses to Delete Non-Empty Bucket",
        "what_it_actually_means": "S3 buckets with even a single hidden 0-byte file, object version, or incomplete multipart upload cannot be deleted via a simple delete-bucket call.",
        "empathy_note": "A classic safety feature that feels like a trap when you just want to tidy up your test bucket. AWS is protecting your data, but making you work for it.",
        "quick_fix_cli": "# Empty all objects and object versions in one go:\naws s3 rm s3://<YOUR_BUCKET_NAME> --recursive\n\n# Then safely delete the empty bucket:\naws s3 rb s3://<YOUR_BUCKET_NAME>",
        "preventative_tip": "If bucket versioning was ever enabled, delete object versions using `aws s3api delete-objects` with a lifecycle rule.",
    },
    {
        "pattern": r"(SignatureDoesNotMatch|The request signature we calculated does not match)",
        "category": "Authentication",
        "title": "Clock Skew or Key Typo",
        "what_it_actually_means": "Either your AWS secret key has a sneaky leading/trailing space or typo, or your computer's local clock is out of sync with UTC by more than 15 minutes.",
        "empathy_note": "This error looks terrifying and cryptographic, but 8 out of 10 times it's literally just your laptop clock being 4 minutes fast after waking up from sleep mode!",
        "quick_fix_cli": "# 1. Sync system clock:\nsudo timedatectl set-ntp true\n\n# 2. Re-check credentials in ~/.aws/credentials (watch out for spaces):\naws configure list",
        "preventative_tip": "Never copy-paste secret keys into bash commands with special characters ($ or !) that get evaluated by your shell.",
    },
    {
        "pattern": r"(LimitExceededException|VcpuLimitExceeded|TooManyBuckets)",
        "category": "Service Quotas",
        "title": "Hit Default AWS Account Limit",
        "what_it_actually_means": "You didn't do anything wrong—your account just hit an arbitrary default safety cap that AWS sets for new or default accounts (like a max of 32 vCPUs or 5 VPCs).",
        "empathy_note": "Think of this as AWS giving you training wheels so you don't accidentally bankrupt yourself. It's not a bug!",
        "quick_fix_cli": "# Request an immediate quota increase via AWS Service Quotas CLI:\naws service-quotas request-service-quota-increase \\\n  --service-code ec2 \\\n  --quota-code L-1216C47A \\\n  --desired-value 64",
        "preventative_tip": "Request quota increases a couple of days before launching a big test or production migration.",
    },
    {
        "pattern": r"(VolumeInUse|volume .* is still attached to)",
        "category": "EBS Storage",
        "title": "Volume Still Hooked to an EC2 Instance",
        "what_it_actually_means": "You tried to delete an EBS drive while it's still attached to an EC2 instance (even if that instance is currently stopped).",
        "empathy_note": "AWS is stopping you from pulling the rug out from under your operating system. Super safe, just requires one extra unmount/detach step.",
        "quick_fix_cli": "# Detach volume first (safe detach):\naws ec2 detach-volume --volume-id <VOL_ID>\n\n# Wait for state to become 'available', then delete:\naws ec2 delete-volume --volume-id <VOL_ID>",
        "preventative_tip": "Set 'DeleteOnTermination: true' on root volumes if you want them to automatically clean up when you terminate test EC2 instances.",
    },
]


def translate_aws_error(raw_error_text: str) -> ErrorTranslation:
    """
    Takes any raw AWS error string or traceback and translates it
    into empathetic, actionable advice.
    """
    clean_text = raw_error_text.strip()

    for item in ERROR_KNOWLEDGE_BASE:
        if re.search(item["pattern"], clean_text, re.IGNORECASE):
            return ErrorTranslation(
                raw_error=clean_text,
                category=item["category"],
                what_aws_said=item["title"],
                what_it_actually_means=item["what_it_actually_means"],
                empathy_note=item["empathy_note"],
                quick_fix_cli=item["quick_fix_cli"],
                preventative_tip=item["preventative_tip"],
            )

    # General fallback for unrecognized AWS errors
    return ErrorTranslation(
        raw_error=clean_text,
        category="General AWS Exception",
        what_aws_said="Cryptic AWS SDK / API Response",
        what_it_actually_means=(
            "AWS returned an error condition that often relates to missing parameters, "
            "insufficient IAM policies, or state mismatch on the target resource."
        ),
        empathy_note="Cloud engineering is 20% building and 80% deciphering API responses. Take a breath—we will get this working.",
        quick_fix_cli="# Inspect detailed error with debug logging enabled:\naws --debug <command>",
        preventative_tip="Run commands with `--dry-run` flag first when testing changes in EC2.",
    )
