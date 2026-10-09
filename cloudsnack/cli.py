"""
CloudSnack - Command Line Interface
Run:
  python3 -m cloudsnack.cli scan
  python3 -m cloudsnack.cli chat
  python3 -m cloudsnack.cli translate "error message"
  python3 -m cloudsnack.cli demo
  python3 -m cloudsnack.cli snackify 45.50
"""

import argparse
import sys
from .agent import CloudSnackAgent
from .ui import print_banner, print_first_run_welcome
from .snackonomics import calculate_snack_equivalents


def main():
    parser = argparse.ArgumentParser(
        prog="cloudsnack",
        description="🍪 CloudSnack - Your guilt-free AWS cloud hygiene & anti-bill-shock pal.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Run a non-destructive audit and view today's Snack Tray")
    scan_parser.add_argument("--region", default="us-east-1", help="AWS region to scan (default: us-east-1)")
    scan_parser.add_argument("--demo", action="store_true", help="Run in simulator/demo mode without calling live AWS")

    # chat subcommand
    chat_parser = subparsers.add_parser("chat", help="Launch interactive conversational agent REPL")
    chat_parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    chat_parser.add_argument("--demo", action="store_true", help="Force simulator mode for local testing")

    # translate subcommand
    trans_parser = subparsers.add_parser("translate", help="Translate an intimidating AWS error into plain English")
    trans_parser.add_argument("error_text", nargs="+", help="The raw AWS error message or exception text")

    # snackify subcommand
    snack_parser = subparsers.add_parser("snackify", help="Convert dollar amounts into delicious snack equivalents")
    snack_parser.add_argument("amount", type=float, help="Monthly cost in USD (e.g. 45.00)")

    # demo subcommand
    demo_parser = subparsers.add_parser("demo", help="Run an automated walkthrough of all CloudSnack capabilities")

    args = parser.parse_args()

    if not args.command:
        # Default behavior: run banner and start chat or scan
        agent = CloudSnackAgent(use_simulator=True)
        agent.interactive_repl()
        return

    if args.command == "scan":
        print_banner()
        agent = CloudSnackAgent(region=args.region, use_simulator=args.demo)
        agent.display_audit_tray()

    elif args.command == "chat":
        agent = CloudSnackAgent(region=args.region, use_simulator=args.demo)
        agent.interactive_repl()

    elif args.command == "translate":
        error_msg = " ".join(args.error_text)
        agent = CloudSnackAgent(use_simulator=True)
        agent.translate_error(error_msg)

    elif args.command == "snackify":
        eq = calculate_snack_equivalents(args.amount)
        print_banner()
        print(f"💰 **Monthly Waste:** ${args.amount:.2f}")
        print(f"🍱 **Snack Breakdown:** {eq['primary_emoji']} ≈ {eq['monthly_count']} {eq['primary_snack']}s / month")
        print(f"☕ **Weekly Equivalent:** {eq['weekly_count']} per week (${eq['weekly_usd']:.2f}/wk)")
        print(f"💡 **Commentary:** {eq['commentary']}\n")
        print("Detailed Menu Breakdown:")
        for item in eq["menu_breakdown"]:
            print(f"  {item['emoji']} {item['name']:<24}: {item['count_monthly']} items/mo (@ ${item['price_each']:.2f} each)")
        print()

    elif args.command == "demo":
        run_full_demo()


def run_full_demo():
    """Runs a complete guided demo with realistic interactions."""
    import time

    print_banner()
    print_first_run_welcome()
    time.sleep(1)

    print("\n[STEP 1/3] 🔍 Running safe, read-only Cloud Hygiene Scan (Simulator Mode)...")
    agent = CloudSnackAgent(use_simulator=True)
    time.sleep(1)
    agent.display_audit_tray()

    print("\n[STEP 2/3] 💬 Asking Amazon Bedrock for contextual guidance...")
    print("User Query: 'Why is my NAT Gateway costing so much and what is the safest way to replace it?'")
    time.sleep(1)
    resp = agent.chat("Why is my NAT Gateway costing so much and what is the safest way to replace it?")
    print(f"\nCloudSnack Response:\n{resp}\n")

    print("[STEP 3/3] 💥 Demonstrating the Cryptic AWS Error Translator...")
    time.sleep(1)
    sample_error = "ClientError: An error occurred (InvalidParameterCombination) when calling the CreateDBInstance operation: AllocatedStorage 10 is less than minimum 20 for storage type gp3"
    agent.translate_error(sample_error)

    print("🎉 Demo complete! That's how CloudSnack turns cloud anxiety into pure builder joy.\n")


if __name__ == "__main__":
    main()
