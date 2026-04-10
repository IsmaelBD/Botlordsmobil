#!/usr/bin/env python3
"""
main.py — Lords Mobile Bot — Entry Point
Usage: python main.py [--mode web|cli|gather|redeem]
"""

import sys
import argparse
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from brain.fsm.engine import FSMBotEngine
from modules.gatherer.bot import GathererBot
from modules.redeemer.bot import RedeemerBot
from ui.web.app import app, socketio, set_engine, set_gatherer, set_redeemer


def mode_web():
    """Launch web dashboard."""
    from ui.web.app import app, socketio
    engine = FSMBotEngine()
    gatherer = GathererBot()
    redeemer = RedeemerBot()
    set_engine(engine)
    set_gatherer(gatherer)
    set_redeemer(redeemer)
    print("[*] Starting web dashboard on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)


def mode_cli():
    """Interactive CLI mode."""
    engine = FSMBotEngine()
    gatherer = GathererBot()
    redeemer = RedeemerBot()

    print("=" * 50)
    print("  Lords Mobile Bot — CLI Mode")
    print("=" * 50)
    print(f"  Game detected: {bool(engine.radar.clients)}")
    print(f"  Window found:  {bool(engine.hands.hwnd)}")
    print()

    while True:
        print("\n[MENU]")
        print("1. Start FSM Engine (auto mode)")
        print("2. Gather resources (manual)")
        print("3. Redeem gift code")
        print("4. Status check")
        print("5. Exit")
        choice = input("> ")

        if choice == "1":
            engine.start()
        elif choice == "2":
            targets = [(522, 356)]
            gatherer.run_cycle(targets)
        elif choice == "3":
            code = input("Gift code: ").strip() or "LM2026"
            redeemer.redeem(code)
        elif choice == "4":
            print(json.dumps(engine.status, indent=2))
        elif choice == "5":
            engine.stop()
            break


def mode_gather():
    """Quick gather mode."""
    gatherer = GathererBot()
    targets = [(522, 356)]  # Default target — should come from config
    gatherer.run_cycle(targets)


def mode_redeem():
    """Quick redeem mode."""
    redeemer = RedeemerBot()
    result = redeemer.redeem()
    print(f"Redeem result: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lords Mobile Bot")
    parser.add_argument("--mode", choices=["web", "cli", "gather", "redeem"], default="cli")
    args = parser.parse_args()

    if args.mode == "web":
        mode_web()
    elif args.mode == "cli":
        mode_cli()
    elif args.mode == "gather":
        mode_gather()
    elif args.mode == "redeem":
        mode_redeem()
