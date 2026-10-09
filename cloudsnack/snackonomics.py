"""
CloudSnack - Snackonomics Engine
Converts cold AWS cloud waste into relatable, delightful snack units.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SnackUnit:
    name: str
    emoji: str
    price_usd: float
    description: str


SNACK_MENU: List[SnackUnit] = [
    SnackUnit("Oat Milk Flat White", "☕", 5.25, "Artisanal barista coffee with silky microfoam"),
    SnackUnit("NYC Pepperoni Slice", "🍕", 4.00, "Classic hot slice with crispy crust"),
    SnackUnit("Flaky Butter Croissant", "🥐", 3.75, "Golden bakery croissant fresh from the oven"),
    SnackUnit("Street Taco", "🌮", 3.25, "Carne asada taco with cilantro and lime"),
    SnackUnit("Brown Sugar Boba Milk", "🧋", 6.50, "Chewy tapioca pearls in caramelized milk"),
    SnackUnit("Gourmet Truffle Chips", "🥨", 2.75, "Kettle cooked chips with sea salt"),
    SnackUnit("Chocolate Chip Cookie", "🍪", 2.50, "Warm gooey bakery cookie with melted chips"),
]


def calculate_snack_equivalents(monthly_usd: float) -> Dict[str, any]:
    """
    Given a monthly cost in USD, calculates equivalent snacks per month and per week.
    """
    if monthly_usd <= 0:
        return {
            "monthly_usd": 0.0,
            "weekly_usd": 0.0,
            "daily_usd": 0.0,
            "primary_snack": SNACK_MENU[0].name,
            "primary_emoji": SNACK_MENU[0].emoji,
            "monthly_count": 0,
            "weekly_count": 0,
            "commentary": "Your cloud is lean and clean! Zero crumbs detected. 🎉",
            "menu_breakdown": [],
        }

    weekly_usd = monthly_usd / 4.33
    daily_usd = monthly_usd / 30.42

    # Pick the best-fitting primary snack
    primary = SNACK_MENU[0]  # default to coffee
    if monthly_usd < 10.0:
        primary = SNACK_MENU[6]  # cookies
    elif monthly_usd < 25.0:
        primary = SNACK_MENU[1]  # pizza
    elif monthly_usd < 60.0:
        primary = SNACK_MENU[0]  # coffee
    else:
        primary = SNACK_MENU[4]  # boba / lunch feast

    monthly_count = round(monthly_usd / primary.price_usd, 1)
    weekly_count = round(weekly_usd / primary.price_usd, 1)

    # Commentary with humor & empathy
    if monthly_usd < 10.0:
        commentary = (
            f"A light snack! That's roughly {int(monthly_count) or 1} {primary.emoji} {primary.name}s "
            "per month. Not a disaster, but hey, free snacks are free snacks."
        )
    elif monthly_usd < 50.0:
        commentary = (
            f"A solid cafe tab! That's {int(weekly_count) or 1} {primary.emoji} {primary.name}s "
            f"every single week ({monthly_count} per month). You're basically buying lunch for idle servers."
        )
    elif monthly_usd < 150.0:
        commentary = (
            f"Whoa, gourmet banquet alert! That's {monthly_count} {primary.emoji} {primary.name}s a month. "
            "Your idle cloud infrastructure is eating better than most startup founders."
        )
    else:
        commentary = (
            f"🚨 Michelin-Star Feast! At ${monthly_usd:,.2f}/mo, this is {monthly_count} {primary.emoji} "
            f"{primary.name}s. Let's put this AWS account on a gentle, delightful diet."
        )

    breakdown = []
    for snack in SNACK_MENU:
        cnt = round(monthly_usd / snack.price_usd, 1)
        breakdown.append({
            "name": snack.name,
            "emoji": snack.emoji,
            "count_monthly": cnt,
            "price_each": snack.price_usd,
        })

    return {
        "monthly_usd": round(monthly_usd, 2),
        "weekly_usd": round(weekly_usd, 2),
        "daily_usd": round(daily_usd, 2),
        "primary_snack": primary.name,
        "primary_emoji": primary.emoji,
        "monthly_count": monthly_count,
        "weekly_count": weekly_count,
        "commentary": commentary,
        "menu_breakdown": breakdown,
    }


def format_snack_summary(monthly_usd: float) -> str:
    """Returns a short, delightful single-line snack badge."""
    eq = calculate_snack_equivalents(monthly_usd)
    if monthly_usd <= 0:
        return "✨ Clean Cloud (0 crumbs)"
    return f"{eq['primary_emoji']} ≈ {eq['monthly_count']} {eq['primary_snack']}s/mo (${monthly_usd:.2f})"
