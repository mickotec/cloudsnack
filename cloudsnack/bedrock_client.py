"""
CloudSnack - Amazon Bedrock Converse Client
Integrates with Amazon Bedrock using the unified Converse API.
Includes an intelligent fallback simulator for offline / demo environments.
"""

import os
from typing import List, Dict, Any, Optional


SYSTEM_PROMPT = """You are CloudSnack, a warm, witty, and deeply empathetic AI cloud hygiene companion.
Your mission is to help developers, solo builders, and startup teams manage their AWS resources without anxiety, shame, or surprise bills.

Key Personality Guidelines:
1. 'Snackonomics': Whenever discussing dollar costs, convert them into delicious, tangible snack units (oat milk lattes, pizza slices, croissants, street tacos, boba).
2. 'Zero Shame & Empathy': Never scold a user for leaving a resource running. Acknowledge that cloud development is complex and everyone makes mistakes.
3. 'Mercy Mode': Always prioritize safe, non-destructive, reversible actions. Suggest dry-run commands, pre-delete snapshots, and clear rollbacks.
4. 'Plain English': Decrypt acronyms (EBS, EIP, ENI, NAT-GW) into plain human language.
5. Be concise, punchy, cheerful, and actionable.
"""


class BedrockAgentClient:
    """
    Connects to Amazon Bedrock Converse API with graceful offline simulator fallback.
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name: str = "us-east-1",
    ):
        self.model_id = model_id
        self.region_name = region_name
        self.has_live_bedrock = False
        self._bedrock_client = None

        try:
            import boto3  # type: ignore
            # Check if AWS credentials exist in environment or default profile
            session = boto3.Session(region_name=self.region_name)
            creds = session.get_credentials()
            if creds and creds.access_key:
                self._bedrock_client = session.client("bedrock-runtime", region_name=self.region_name)
                self.has_live_bedrock = True
        except Exception:
            self.has_live_bedrock = False

    def converse(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Sends conversation history to Amazon Bedrock Converse API or runs local fallback.
        """
        if self.has_live_bedrock and self._bedrock_client:
            try:
                system_text = [{"text": system_prompt or SYSTEM_PROMPT}]
                response = self._bedrock_client.converse(
                    modelId=self.model_id,
                    messages=messages,
                    system=system_text,
                    inferenceConfig={"temperature": 0.7, "maxTokens": 1000},
                )
                output_message = response.get("output", {}).get("message", {})
                content = output_message.get("content", [])
                if content and "text" in content[0]:
                    return content[0]["text"]
            except Exception as e:
                # If Bedrock permissions are not enabled for this specific model or token expired:
                return self._simulate_bedrock_response(messages, error_note=str(e))

        return self._simulate_bedrock_response(messages)

    def _simulate_bedrock_response(self, messages: List[Dict[str, Any]], error_note: Optional[str] = None) -> str:
        """
        Intelligent local simulation that responds in CloudSnack's signature voice.
        Used when offline, in unit tests, or during live demos without active Bedrock keys.
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content", [])
                if isinstance(content, list) and content and "text" in content[0]:
                    last_user_msg = content[0]["text"]
                elif isinstance(content, str):
                    last_user_msg = content
                break

        query = last_user_msg.lower()

        if "nat" in query:
            return (
                "☕ Ah, the infamous NAT Gateway! AWS charges roughly $32.40/month baseline ($0.045/hr) "
                "just to keep it alive—even if zero bytes pass through it. That's about 6 oat milk flat whites!\n\n"
                "💡 **Mercy Mode Recommendation**:\n"
                "1. If your private EC2 instances only need to talk to S3 or DynamoDB, replace the NAT Gateway "
                "with free **VPC Gateway Endpoints**.\n"
                "2. If you don't need outbound internet right now, delete the NAT Gateway:\n"
                "   `aws ec2 delete-nat-gateway --nat-gateway-id <ID>`\n\n"
                "You just bought yourself a weekly coffee budget back!"
            )
        elif "ebs" in query or "volume" in query or "disk" in query:
            return (
                "🍕 Unattached EBS volumes are classic cloud crumbs! When you terminate an EC2 instance, "
                "secondary volumes stay behind in 'available' state, quietly billing $0.08–$0.10 per GB every month.\n\n"
                "A 100 GB volume is $8.00/month (2 NYC pepperoni pizza slices).\n\n"
                "🛡️ **Safe Cleanup Recipe**:\n"
                "```bash\n"
                "# 1. Take a safe snapshot just in case:\n"
                "aws ec2 create-snapshot --volume-id <VOL_ID> --description 'Safety backup'\n\n"
                "# 2. Safely delete the orphaned volume:\n"
                "aws ec2 delete-volume --volume-id <VOL_ID>\n"
                "```\n"
                "Snapshot storage is ~70% cheaper than keeping the active volume, and your mind stays at peace."
            )
        elif "rds" in query or "database" in query:
            return (
                "🥐 Here is one of AWS's sneakiest secrets: When you 'stop' an RDS instance, AWS automatically "
                "**restarts it after 7 days**! Plus, you still pay for allocated gp3 storage while it's stopped.\n\n"
                "If it's an old test database eating $11.50/mo (3 fresh croissants):\n"
                "```bash\n"
                "aws rds create-db-snapshot --db-instance-identifier my-db --db-snapshot-identifier my-db-backup\n"
                "aws rds delete-db-instance --db-instance-identifier my-db --skip-final-snapshot\n"
                "```\n"
                "Snapshots can be restored anytime if you need the data back!"
            )
        elif "error" in query or "translate" in query:
            return (
                "🔍 AWS errors can look like encrypted tax documents! Tell me the exact error message "
                "(or run `cloudsnack translate \"<error>\"`), and I'll translate it into plain English, "
                "tell you why AWS is grumbling, and give you the copy-paste fix."
            )
        else:
            return (
                f"🍪 Hey there! CloudSnack at your service. I'm looking at your cloud environment through "
                f"the lens of **Snackonomics** (turning cloud waste into coffee, tacos, and pizza).\n\n"
                f"You asked: *\"{last_user_msg}\"*\n\n"
                f"Here is what I recommend:\n"
                f"• Run a quick non-destructive audit: type `scan` or run `cloudsnack scan`\n"
                f"• Ask me about high-cost items like NAT Gateways, idle RDS, or unattached EBS volumes\n"
                f"• Paste any scary AWS error and I'll decrypt it with zero judgment!\n\n"
                f"What snack budget shall we reclaim today?"
            )
