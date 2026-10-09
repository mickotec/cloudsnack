#!/usr/bin/env python3
"""
CloudSnack - Quick Demo Runner
Run this directly with: python3 run_demo.py
"""

import sys
import os

# Ensure package root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cloudsnack.cli import run_full_demo

if __name__ == "__main__":
    run_full_demo()
