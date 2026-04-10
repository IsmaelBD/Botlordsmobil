#!/usr/bin/env python3
"""
run_desktop.py — Launch Lords Mobile Bot Desktop UI
Usage: python run_desktop.py
Requires: PyQt5 (pip install PyQt5)
"""

import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.desktop.main_window import main

if __name__ == "__main__":
    main()
