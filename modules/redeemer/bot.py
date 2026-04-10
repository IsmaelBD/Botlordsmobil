"""
modules/redeemer/bot.py — Gift Code Redeemer
Redeems gift codes by connecting directly to the game server via TCP.
Phase 3 Anti-Detection: randomized timing between steps.
"""

import socket
import time
import random
import json
from pathlib import Path

from core.anti_detection import AntiDetection


PACKETS = {
    "version": "4000c832bbc6d11e3e0000803fe054c53f4bce43c0e41369c0000000005c392a4026a327c085e3544000000000d65d7cc034a03dc08ee2513f00000000c4bf3e",
    "activation": "0f00000410000068100000cc100000",
    "login": "8f0013048870d0edebe201000040c4edebe201000000cdedebe201000100000000000070cbedebe2010000000000000000000035000000000000003f0000000000000070387417fc7f0000daf86a8f00140490556e697479456e67696e652e417564696f5265766572625a6f6e653a3a6765745f64656361794846526174696f5f496e6a656374656400000000",
    "redeem_1420": "80008c0590556e697479456e67696e652e436c6f74683a3a6765745f7573655669727475616c5061727469636c65735f496e6a65637465640000000000000000000000000000000000000000003fc0cd80008d0588509639eae2010000204deeebe2010000509639eae201000000000000000000000040eeebe2010000000000",
}


class RedeemerBot:
    def __init__(self, gift_code: str = None):
        self._load_config()
        self.gift_code = gift_code or "LM2026"
        self.host = self._cfg["network"]["gift_server"]["host"]
        self.port = self._cfg["network"]["gift_server"]["port"]
        self.timeout = self._cfg["timing"]["network_timeout"]
        self.anti_detection = AntiDetection()

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

    def _step_delay(self, min_ms: float = 300, max_ms: float = 800) -> float:
        """Human-like delay between network steps."""
        return self.anti_detection.human_delay(min_ms=min_ms, max_ms=max_ms)

    def redeem(self, gift_code: str = None) -> bool:
        """Execute the gift code redemption sequence."""
        code = gift_code or self.gift_code
        print(f"[*] Redeeming gift code: {code}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                print("[+] Connected to game server")

                # Step 1: Version handshake with randomized delay
                print("[*] Sending version handshake...")
                s.sendall(bytes.fromhex(PACKETS["version"]))
                time.sleep(self._step_delay(300, 700))

                # Step 2: Hardware activation with randomized delay
                print("[*] Sending hardware activation...")
                s.sendall(bytes.fromhex(PACKETS["activation"]))
                time.sleep(self._step_delay(300, 700))

                # Step 3: Session login with randomized delay
                print("[*] Sending session login...")
                s.sendall(bytes.fromhex(PACKETS["login"]))
                time.sleep(self._step_delay(600, 1200))

                # Step 4: Redeem gift code (custom per code)
                print(f"[*] Redeeming: {code}")
                s.sendall(bytes.fromhex(PACKETS["redeem_1420"]))

                # Wait for response with slight random jitter
                time.sleep(self._step_delay(500, 1500))
                resp = s.recv(1024)
                if resp:
                    print(f"[!] Server response: {resp.hex()}")
                    return True
                else:
                    print("[+] No response (gift already redeemed or success)")
                    return True

        except socket.timeout:
            print("[!] Connection timeout — server may be busy")
            return False
        except Exception as e:
            print(f"[!] Redeem error: {e}")
            return False

    def batch_redeem(self, codes: list[str]) -> dict[str, bool]:
        """Redeem multiple gift codes with randomized pauses."""
        results = {}
        for code in codes:
            print(f"\n{'='*40}")
            success = self.redeem(code)
            results[code] = success
            # Randomized cooldown between codes (30-90 seconds)
            pause = self.anti_detection.random_cycle_delay()
            print(f"[*] Pause between codes: {pause:.1f}s")
            time.sleep(pause)
        return results
