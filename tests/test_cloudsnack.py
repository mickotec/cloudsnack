"""
Unit tests for CloudSnack modules:
- snackonomics
- translator
- scanner
- bedrock_client
- agent
"""

import unittest
from cloudsnack.snackonomics import calculate_snack_equivalents, format_snack_summary
from cloudsnack.translator import translate_aws_error
from cloudsnack.scanner import CloudScanner
from cloudsnack.bedrock_client import BedrockAgentClient
from cloudsnack.agent import CloudSnackAgent


class TestCloudSnack(unittest.TestCase):

    def test_snackonomics_zero(self):
        eq = calculate_snack_equivalents(0.0)
        self.assertEqual(eq["monthly_usd"], 0.0)
        self.assertEqual(eq["monthly_count"], 0)
        self.assertIn("Clean", format_snack_summary(0.0))

    def test_snackonomics_positive(self):
        eq = calculate_snack_equivalents(52.50)
        self.assertEqual(eq["monthly_usd"], 52.50)
        self.assertGreater(eq["monthly_count"], 0)
        self.assertIn("Oat Milk", eq["primary_snack"])
        self.assertGreater(len(eq["menu_breakdown"]), 3)

    def test_error_translator_vpc_dependency(self):
        err = "ClientError: An error occurred (ResourceInUseException) when calling DeleteVpc: The vpc 'vpc-123' has dependencies"
        t = translate_aws_error(err)
        self.assertEqual(t.category, "VPC & Networking")
        self.assertIn("hidden dependencies", t.what_aws_said.lower())
        self.assertIn("aws ec2 describe-network-interfaces", t.quick_fix_cli)

    def test_error_translator_s3_bucket_not_empty(self):
        err = "An error occurred (BucketNotEmpty) when calling the DeleteBucket operation"
        t = translate_aws_error(err)
        self.assertEqual(t.category, "S3 Storage")
        self.assertIn("aws s3 rm", t.quick_fix_cli)

    def test_error_translator_general_fallback(self):
        err = "SomeRandomServiceError: Something weird happened in code 500"
        t = translate_aws_error(err)
        self.assertEqual(t.category, "General AWS Exception")
        self.assertIn("debug", t.quick_fix_cli)

    def test_scanner_simulator(self):
        scanner = CloudScanner(use_simulator=True)
        findings = scanner.scan_all()
        self.assertGreaterEqual(len(findings), 3)
        res_types = [f.resource_type for f in findings]
        self.assertIn("NAT Gateway", res_types)
        self.assertIn("Unattached EBS Volume", res_types)

    def test_bedrock_converse_simulator(self):
        client = BedrockAgentClient(region_name="us-east-1")
        # Simulator fallback
        resp = client.converse([{"role": "user", "content": [{"text": "Why is my NAT gateway expensive?"}]}])
        self.assertIn("NAT Gateway", resp)
        self.assertIn("flat white", resp.lower())

    def test_agent_integration(self):
        agent = CloudSnackAgent(use_simulator=True)
        findings = agent.audit()
        self.assertGreater(len(findings), 0)

        # Test command shortcut
        snack_reply = agent.chat("convert $40 into pizza")
        self.assertIn("Snack Breakdown", snack_reply)


if __name__ == "__main__":
    unittest.main()
