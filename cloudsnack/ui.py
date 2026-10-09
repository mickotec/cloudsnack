"""
CloudSnack - Terminal UI & Presentation Engine
Renders colorful ASCII art banners, delicious Snack Trays, and Mercy Mode cards.
Uses pure ANSI formatting with zero mandatory dependencies.
"""

import sys
from typing import List
from .scanner import WasteFinding
from .snackonomics import calculate_snack_equivalents
from .translator import ErrorTranslation


# ANSI Color codes
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
RESET = "\033[0m"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

BG_MAGENTA = "\033[45m"
BG_BLUE = "\033[44m"


def print_banner():
    banner = f"""
{YELLOW}   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   {BOLD}{MAGENTA}🍪  C L O U D S N A C K  ☕{RESET}{YELLOW}                                 │
   │   {CYAN}Your guilt-free AWS cloud hygiene & anti-bill-shock pal{RESET}{YELLOW}    │
   │                                                              │
   └──────────────────────────────────────────────────────────────┘{RESET}
"""
    print(banner)


def print_first_run_welcome():
    print(f"{BOLD}👋 Welcome to CloudSnack!{RESET}")
    print(f"{DIM}Cloud monitoring shouldn't feel like a corporate audit or a heart attack.{RESET}")
    print(f"Here is our promise to you:")
    print(f"  {GREEN}✓{RESET} 100% Read-Only: We NEVER touch or delete your AWS resources.")
    print(f"  {GREEN}✓{RESET} Zero Guilt: We translate cloud waste into delicious coffees & snacks.")
    print(f"  {GREEN}✓{RESET} Mercy Mode: Every finding includes safe, copy-paste rollback commands.")
    print(f"  {GREEN}✓{RESET} Bedrock Powered: Deep AWS intelligence with conversational clarity.\n")


def render_snack_tray(findings: List[WasteFinding]):
    """Renders an appetizing, beautifully formatted Snack Tray table."""
    total_usd = sum(f.monthly_cost_usd for f in findings)
    eq = calculate_snack_equivalents(total_usd)

    print(f"{BOLD}{CYAN}═════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD} 🍱 TODAY'S CLOUD SNACK TRAY (Audit Summary){RESET}")
    print(f"{BOLD}{CYAN}═════════════════════════════════════════════════════════════════════════════════{RESET}")

    if not findings:
        print(f"\n{GREEN}✨ Crisp & Clean! No idle crumbs found in your AWS account. You're running lean!{RESET}\n")
        return

    print(f"\n{BOLD}{'RESOURCE TYPE':<24} {'RESOURCE ID':<26} {'COST/MO':<10} {'SNACK EQUIVALENT'}{RESET}")
    print(f"{DIM}{'-'*24} {'-'*26} {'-'*10} {'-'*20}{RESET}")

    for f in findings:
        cost_str = f"${f.monthly_cost_usd:.2f}"
        print(f"{WHITE}{f.resource_type:<24}{RESET} {YELLOW}{f.resource_id:<26}{RESET} {RED}{cost_str:<10}{RESET} {f.snack_badge}")

    print(f"{DIM}{'-'*81}{RESET}")
    print(f"{BOLD}TOTAL POTENTIAL MONTHLY WASTE:{RESET} {BOLD}{RED}${total_usd:.2f} / month{RESET}")
    print(f"{BOLD}SNACKONOMICS RECAP:{RESET} {YELLOW}{eq['primary_emoji']} ≈ {eq['monthly_count']} {eq['primary_snack']}s / month!{RESET}")
    print(f"{ITALIC}{CYAN}👉 {eq['commentary']}{RESET}\n")

    print(f"{BOLD}{MAGENTA}🛡️  MERCY MODE: 1-CLICK SAFE REMEDIATION RECIPES{RESET}")
    print(f"{DIM}(Review these recipes below—dry-run and safe snapshot commands included){RESET}\n")

    for i, f in enumerate(findings, 1):
        print(f"{BOLD}[{i}] {f.resource_type}: {YELLOW}{f.resource_id}{RESET}")
        print(f"    {ITALIC}{f.mercy_explanation}{RESET}")
        print(f"    {GREEN}Safe Fix CLI:{RESET}")
        for line in f.safe_remediation_cli.split("\n"):
            print(f"      {DIM}{line}{RESET}")
        print()


def render_error_translation(t: ErrorTranslation):
    """Renders a friendly card translating a scary AWS error."""
    print(f"\n{BOLD}{YELLOW}┌─────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BOLD}{YELLOW}│ 🔍 AWS ERROR TRANSLATOR (Plain English + Empathy)           │{RESET}")
    print(f"{BOLD}{YELLOW}└─────────────────────────────────────────────────────────────┘{RESET}\n")

    print(f"{BOLD}{RED}💥 What AWS Said:{RESET} {DIM}{t.raw_error}{RESET}\n")
    print(f"{BOLD}{CYAN}🏷️  Category:{RESET} {t.category} ({t.what_aws_said})")
    print(f"{BOLD}{GREEN}🗣️  What It Actually Means:{RESET}\n   {t.what_it_actually_means}\n")
    print(f"{BOLD}{MAGENTA}💖 The Empathy Check:{RESET}\n   {ITALIC}{t.empathy_note}{RESET}\n")
    print(f"{BOLD}{YELLOW}⚡ Safe Quick Fix (Copy-Paste):{RESET}")
    for line in t.quick_fix_cli.split("\n"):
        print(f"   {WHITE}{line}{RESET}")
    print(f"\n{BOLD}{BLUE}🛡️  Preventative Wisdom:{RESET}\n   {t.preventative_tip}\n")
