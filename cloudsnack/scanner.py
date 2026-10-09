"""
CloudSnack - Safe Read-Only Cloud Hygiene Scanner
Audits AWS resources for idle waste without making ANY destructive changes.
Supports both live AWS boto3 scans and an interactive simulator mode.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import os

from .snackonomics import calculate_snack_equivalents, format_snack_summary


@dataclass
class WasteFinding:
    resource_id: str
    resource_type: str
    region: str
    description: str
    monthly_cost_usd: float
    snack_badge: str
    safe_remediation_cli: str
    mercy_explanation: str
    details: Dict[str, str] = field(default_factory=dict)


class CloudScanner:
    """
    Safe read-only auditor for AWS cloud environments.
    Guaranteed NEVER to mutate or delete resources.
    """

    def __init__(self, region: str = "us-east-1", use_simulator: bool = False):
        self.region = region
        self.use_simulator = use_simulator
        self._boto3_available = False

        if not self.use_simulator:
            try:
                import boto3  # type: ignore
                self._boto3 = boto3
                self._boto3_available = True
            except ImportError:
                # Graceful fallback to simulator if boto3 is not installed
                self.use_simulator = True

    def scan_all(self) -> List[WasteFinding]:
        """Runs all non-destructive audits and returns aggregated findings."""
        if self.use_simulator:
            return self._run_simulator_scan()

        findings: List[WasteFinding] = []
        try:
            findings.extend(self._scan_live_ebs())
            findings.extend(self._scan_live_nat_gateways())
            findings.extend(self._scan_live_elastic_ips())
        except Exception as e:
            # If live scan fails (e.g. no AWS credentials in env), gracefully fall back to demo
            print(f"⚠️ Live AWS scan encountered an issue ({e}). Serving demo tray so you can see CloudSnack in action!")
            return self._run_simulator_scan()

        return findings

    def _run_simulator_scan(self) -> List[WasteFinding]:
        """
        Rich, realistic scenario of typical idle resources found in developer accounts.
        """
        findings = [
            WasteFinding(
                resource_id="nat-0a98f12c8b74e11a2",
                resource_type="NAT Gateway",
                region="us-east-1",
                description="Idle NAT Gateway in public subnet with 0 bytes processed over 14 days",
                monthly_cost_usd=32.40,
                snack_badge=format_snack_summary(32.40),
                safe_remediation_cli=(
                    "# Review route tables first to ensure no private EC2 needs internet:\n"
                    "aws ec2 describe-route-tables --filters Name=route.nat-gateway-id,Values=nat-0a98f12c8b74e11a2\n\n"
                    "# When ready, delete the idle NAT Gateway:\n"
                    "aws ec2 delete-nat-gateway --nat-gateway-id nat-0a98f12c8b74e11a2"
                ),
                mercy_explanation=(
                    "NAT Gateways bill $0.045/hour even if 0 packets pass through. "
                    "This single idle gateway is eating ~6 oat milk flat whites every month while sitting idle!"
                ),
                details={"Subnet": "subnet-08c32f", "VpcId": "vpc-0182bb3", "State": "available"},
            ),
            WasteFinding(
                resource_id="vol-03b9841f17e08ba45",
                resource_type="Unattached EBS Volume",
                region="us-east-1",
                description="100 GiB gp3 drive unattached since EC2 termination (State: available)",
                monthly_cost_usd=8.00,
                snack_badge=format_snack_summary(8.00),
                safe_remediation_cli=(
                    "# Create a cheap safety snapshot before deleting:\n"
                    "aws ec2 create-snapshot --volume-id vol-03b9841f17e08ba45 --description 'Pre-delete backup of old dev disk'\n\n"
                    "# Delete the unattached volume safely:\n"
                    "aws ec2 delete-volume --volume-id vol-03b9841f17e08ba45"
                ),
                mercy_explanation=(
                    "When instances are terminated without 'DeleteOnTermination', the EBS disk keeps billing monthly. "
                    "That's 2 hot NY pepperoni pizza slices ($8.00) every month for orphaned data."
                ),
                details={"SizeGiB": "100", "VolumeType": "gp3", "State": "available"},
            ),
            WasteFinding(
                resource_id="eipalloc-017f938c4b6e890cd",
                resource_type="Unassociated Elastic IP",
                region="us-east-1",
                description="Public IPv4 address reserved but not attached to any running EC2 or ENI",
                monthly_cost_usd=3.65,
                snack_badge=format_snack_summary(3.65),
                safe_remediation_cli=(
                    "# Release the unassociated Elastic IP back to the pool:\n"
                    "aws ec2 release-address --allocation-id eipalloc-017f938c4b6e890cd"
                ),
                mercy_explanation=(
                    "AWS charges for Elastic IPs that AREN'T in use to prevent hoarding. "
                    "Releasing this saves 1 flaky butter croissant ($3.65) per month."
                ),
                details={"PublicIp": "54.210.88.19", "NetworkBorderGroup": "us-east-1"},
            ),
            WasteFinding(
                resource_id="dev-postgres-sandbox",
                resource_type="Stopped RDS Instance",
                region="us-east-1",
                description="db.t4g.small PostgreSQL stopped 6 days ago (Storage: 50 GiB gp3)",
                monthly_cost_usd=11.50,
                snack_badge=format_snack_summary(11.50),
                safe_remediation_cli=(
                    "# Take a final DB snapshot:\n"
                    "aws rds create-db-snapshot --db-instance-identifier dev-postgres-sandbox --db-snapshot-identifier dev-postgres-final-snap\n\n"
                    "# Delete the stopped DB to prevent automatic auto-restart after 7 days:\n"
                    "aws rds delete-db-instance --db-instance-identifier dev-postgres-sandbox --skip-final-snapshot"
                ),
                mercy_explanation=(
                    "Sneaky detail: AWS automatically RESTARTS stopped RDS instances after 7 days! "
                    "Plus, you still pay for allocated storage ($11.50/mo = ~3 bakery croissants) while stopped."
                ),
                details={"Engine": "postgres", "Class": "db.t4g.small", "AllocatedStorage": "50GB"},
            ),
        ]
        return findings

    def _scan_live_ebs(self) -> List[WasteFinding]:
        """Safely scans for unattached EBS volumes."""
        findings = []
        ec2 = self._boto3.client("ec2", region_name=self.region)
        resp = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])

        for vol in resp.get("Volumes", []):
            vol_id = vol["VolumeId"]
            size = vol.get("Size", 20)
            vol_type = vol.get("VolumeType", "gp3")
            # Approximate baseline gp3: $0.08 / GB-month
            cost_per_gb = 0.08 if vol_type == "gp3" else 0.10
            monthly_cost = round(size * cost_per_gb, 2)

            findings.append(WasteFinding(
                resource_id=vol_id,
                resource_type="Unattached EBS Volume",
                region=self.region,
                description=f"{size} GiB {vol_type} unattached drive (State: available)",
                monthly_cost_usd=monthly_cost,
                snack_badge=format_snack_summary(monthly_cost),
                safe_remediation_cli=(
                    f"aws ec2 create-snapshot --volume-id {vol_id} --description 'Backup before cleanup'\n"
                    f"aws ec2 delete-volume --volume-id {vol_id}"
                ),
                mercy_explanation="Orphaned volume left behind. Snapshot it for peace of mind, then delete.",
                details={"Size": f"{size}GB", "Type": vol_type},
            ))
        return findings

    def _scan_live_nat_gateways(self) -> List[WasteFinding]:
        """Safely scans for NAT Gateways."""
        findings = []
        ec2 = self._boto3.client("ec2", region_name=self.region)
        resp = ec2.describe_nat_gateways(Filters=[{"Name": "state", "Values": ["available"]}])

        for nat in resp.get("NatGateways", []):
            nat_id = nat["NatGatewayId"]
            # Baseline NAT Gateway cost is $0.045/hr * 720hr = $32.40/mo
            monthly_cost = 32.40
            findings.append(WasteFinding(
                resource_id=nat_id,
                resource_type="NAT Gateway",
                region=self.region,
                description="Active NAT Gateway running (bills $32.40/mo baseline even at 0 traffic)",
                monthly_cost_usd=monthly_cost,
                snack_badge=format_snack_summary(monthly_cost),
                safe_remediation_cli=f"aws ec2 delete-nat-gateway --nat-gateway-id {nat_id}",
                mercy_explanation="If your instances can use VPC endpoints or don't need outbound internet, delete this.",
                details={"VpcId": nat.get("VpcId", "unknown"), "SubnetId": nat.get("SubnetId", "unknown")},
            ))
        return findings

    def _scan_live_elastic_ips(self) -> List[WasteFinding]:
        """Safely scans for unassociated Elastic IP addresses."""
        findings = []
        ec2 = self._boto3.client("ec2", region_name=self.region)
        resp = ec2.describe_addresses()

        for addr in resp.get("Addresses", []):
            if "AssociationId" not in addr and "InstanceId" not in addr:
                alloc_id = addr.get("AllocationId", "unknown")
                pub_ip = addr.get("PublicIp", "unknown")
                monthly_cost = 3.65  # $0.005/hr * 730 hr
                findings.append(WasteFinding(
                    resource_id=alloc_id,
                    resource_type="Unassociated Elastic IP",
                    region=self.region,
                    description=f"Unassociated public IP ({pub_ip})",
                    monthly_cost_usd=monthly_cost,
                    snack_badge=format_snack_summary(monthly_cost),
                    safe_remediation_cli=f"aws ec2 release-address --allocation-id {alloc_id}",
                    mercy_explanation="AWS bills for unused reserved public IPv4 addresses. Release to save.",
                    details={"PublicIp": pub_ip},
                ))
        return findings
