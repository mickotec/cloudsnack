"""
CloudSnack - Your guilt-free AWS cloud hygiene & anti-bill-shock pal.
"""

__version__ = "1.0.0"
__author__ = "CloudSnack Builder"

from .agent import CloudSnackAgent
from .scanner import CloudScanner, WasteFinding
from .translator import translate_aws_error, ErrorTranslation
from .snackonomics import calculate_snack_equivalents, format_snack_summary
