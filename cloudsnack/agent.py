"""
CloudSnack - Core Agent Orchestrator
Coordinates scanning, conversational intelligence via Amazon Bedrock,
error translation, and interactive delight.
"""

from typing import List, Dict, Any, Optional
import os
import sys

from .scanner import CloudScanner, WasteFinding
from .translator import translate_aws_error, ErrorTranslation
from .snackonomics import calculate_snack_equivalents, format_snack_summary
from .bedrock_client import BedrockAgentClient
from .ui import (
    print_banner,
    print_first_run_welcome,
    render_snack_tray,
    render_error_translation,
    BOLD,
    DIM,
    GREEN,
    YELLOW,
    CYAN,
    MAGENTA,
    RESET,
)


class CloudSnackAgent:
    """
    Main conversational agent for CloudSnack.
    """

    def __init__(self, region: str = "us-east-1", use_simulator: bool = False):
        self.region = region
        self.scanner = CloudScanner(region=region, use_simulator=use_simulator)
        self.bedrock = BedrockAgentClient(region_name=region)
        self.conversation_history: List[Dict[str, Any]] = []
        self.cached_findings: Optional[List[WasteFinding]] = None

    def audit(self) -> List[WasteFinding]:
        """Runs the safe read-only audit and caches findings."""
        self.cached_findings = self.scanner.scan_all()
        return self.cached_findings

    def display_audit_tray(self):
        """Audits and renders the beautiful Snack Tray."""
        findings = self.audit()
        render_snack_tray(findings)
        return findings

    def translate_error(self, raw_error: str) -> ErrorTranslation:
        """Translates a raw AWS error into plain English and safe fix."""
        translation = translate_aws_error(raw_error)
        render_error_translation(translation)
        return translation

    def chat(self, user_message: str) -> str:
        """
        Processes a user question or instruction via Bedrock or agent tools.
        """
        lower_msg = user_message.lower().strip()

        # Quick command shortcuts
        if lower_msg in ["scan", "audit", "tray", "snack tray"]:
            self.display_audit_tray()
            return "Here is your fresh Cloud Snack Tray above! 🍱"

        if lower_msg.startswith("translate ") or lower_msg.startswith("error:"):
            err_text = user_message.replace("translate ", "", 1).replace("error:", "", 1).strip()
            self.translate_error(err_text)
            return "Error decrypted above! Let me know if you need help with the command. 🛡️"

        # Check if user asks to convert money to snacks
        if any(w in lower_msg for w in ["snackify", "convert", "in snacks", "in coffee", "in pizza"]):
            import re
            numbers = re.findall(r"\$?\b(\d+(?:\.\d+)?)\b", lower_msg)
            if numbers:
                val = float(numbers[0])
                eq = calculate_snack_equivalents(val)
                return (
                    f"🥐 **${val:.2f} Snack Breakdown**:\n"
                    f"• {eq['primary_emoji']} ≈ {eq['monthly_count']} {eq['primary_snack']}s / month\n"
                    f"• That is about {eq['weekly_count']} per week ({eq['daily_usd']:.2f}/day)\n"
                    f"• *{eq['commentary']}*"
                )

        # Build context for Bedrock
        context_prefix = ""
        if self.cached_findings:
            total_waste = sum(f.monthly_cost_usd for f in self.cached_findings)
            res_summary = ", ".join([f"{f.resource_type} ({f.resource_id})" for f in self.cached_findings])
            context_prefix = (
                f"[System Context: Current account scan shows ${total_waste:.2f}/mo potential waste across: {res_summary}. "
                "Keep answers friendly, constructive, and prioritize non-destructive advice.]\n\n"
            )

        full_prompt = context_prefix + user_message

        # Append to Bedrock converse history format
        self.conversation_history.append({
            "role": "user",
            "content": [{"text": full_prompt}],
        })

        # Ask Bedrock Converse API
        reply = self.bedrock.converse(self.conversation_history)

        self.conversation_history.append({
            "role": "assistant",
            "content": [{"text": reply}],
        })

        return reply

    def interactive_repl(self):
        """Starts an interactive, delightfully styled chat session."""
        print_banner()
        print_first_run_welcome()
        print(f"{CYAN}Commands: 'scan' (Audit Tray) | 'translate <err>' (Decode error) | 'quit' to exit{RESET}\n")

        # Run an initial welcoming scan automatically
        print(f"{YELLOW}⏳ Serving your welcome snack tray...{RESET}\n")
        self.display_audit_tray()

        print(f"\n{BOLD}{MAGENTA}💬 CloudSnack Chat Active:{RESET} Ask questions about your cloud bill, AWS errors, or safe cleanup recipes.")

        while True:
            try:
                user_input = input(f"\n{BOLD}{GREEN}You > {RESET}").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["quit", "exit", "q"]:
                    print(f"\n{YELLOW}🍪 Thanks for using CloudSnack! Keep your cloud clean and your coffee warm.{RESET}\n")
                    break

                response = self.chat(user_input)
                # If chat didn't already render a tray or error card directly:
                if not user_input.lower().startswith("translate ") and user_input.lower() not in ["scan", "audit", "tray"]:
                    print(f"\n{BOLD}{CYAN}CloudSnack >{RESET}\n{response}")

            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{YELLOW}🍪 Bye for now! Stay cloud-snacking.{RESET}\n")
                break
