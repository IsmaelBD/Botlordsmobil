"""
modules/redeemer/bot.py — Gift Code Redeemer
Redeems gift codes by connecting directly to the game server via TCP.
Phase 3 Anti-Detection: randomized timing between steps.
Phase 5: Robust logging, retry with backoff, server rejection detection.
"""

import socket
import time
import random
import json
from pathlib import Path

from core.anti_detection import AntiDetection
from utils.logger import get_logger, ServerResponse


PACKETS = {
    "version": "4000c832bbc6d11e3e0000803fe054c53f4bce43c0e41369c0000000005c392a4026a327c085e3544000000000d65d7cc034a03dc08ee2513f00000000c4bf3e",
    "activation": "0f00000410000068100000cc100000",
    "login": "8f0013048870d0edebe201000040c4edebe201000000cdedebe201000100000000000070cbedebe2010000000000000000000035000000000000003f0000000000000070387417fc7f0000daf86a8f00140490556e697479456e67696e652e417564696f5265766572625a6f6e653a3a6765745f64656361794846526174696f5f496e6a656374656400000000",
    "redeem_1420": "80008c0590556e697479456e67696e652e436c6f74683a3a6765745f7573655669727475616c5061727469636c65735f496e6a65637465640000000000000000000000000000000000000000003fc0cd80008d0588509639eae2010000204deeebe2010000509639eae201000000000000000000000040eeebe2010000000000",
}


class RedeemerBot:
    def __init__(self, gift_code: str = None):
        self.logger = get_logger("lordsbot.redeemer")
        self._load_config()
        self.gift_code = gift_code or "LM2026"
        self.host = self._cfg["network"]["gift_server"]["host"]
        self.port = self._cfg["network"]["gift_server"]["port"]
        self.timeout = self._cfg["timing"]["network_timeout"]
        self.anti_detection = AntiDetection()
        self.logger.info(f"RedeemerBot initialized — server={self.host}:{self.port}")

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

    def _step_delay(self, min_ms: float = 300, max_ms: float = 800) -> float:
        """Human-like delay between network steps."""
        return self.anti_detection.human_delay(min_ms=min_ms, max_ms=max_ms)

    def _connect_and_send(self, steps: list[tuple[str, str]]) -> tuple[bool, str]:
        """
        Connect to server and send a sequence of packets.
        
        Args:
            steps: List of (packet_name, packet_hex) tuples to send in order
            
        Returns:
            Tuple of (had_response, response_hex)
        """
        response_hex = None
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                self.logger.info("Connected to game server")

                for step_name, packet_hex in steps:
                    self.logger.packet_sent(packet_hex, {"step": step_name})
                    s.sendall(bytes.fromhex(packet_hex))
                    time.sleep(self._step_delay())

                # Wait for final response
                time.sleep(self._step_delay(min_ms=500, max_ms=1500))
                resp = s.recv(1024)
                
                if resp:
                    response_hex = resp.hex()
                    self.logger.packet_received(response_hex)
                    return True, response_hex
                else:
                    self.logger.warning("No response from server")
                    return False, None

        except socket.timeout:
            self.logger.error("Connection timeout — server may be busy")
            return False, None
        except ConnectionRefusedError:
            self.logger.error("Connection refused — server may be down")
            return False, None
        except OSError as e:
            self.logger.error(f"Network OS error: {e}")
            return False, None
        except Exception as e:
            self.logger.error(f"Redeem error: {type(e).__name__}: {e}")
            return False, None

    def redeem(self, gift_code: str = None,
               max_retries: int = 3,
               base_delay: float = 5.0) -> dict:
        """
        Execute the gift code redemption sequence with retry logic.

        Returns:
            dict with keys: success (bool), attempts (int), response (str),
                           response_type (ServerResponse), error (str)
        """
        code = gift_code or self.gift_code
        self.logger.info(f"Redeeming gift code: {code}")

        steps = [
            ("version", PACKETS["version"]),
            ("activation", PACKETS["activation"]),
            ("login", PACKETS["login"]),
            ("redeem_1420", PACKETS["redeem_1420"]),
        ]

        # Retry with exponential backoff
        delay = base_delay
        last_response = None
        last_response_type = ServerResponse.UNKNOWN

        for attempt in range(1, max_retries + 1):
            self.logger.info(f"Redemption attempt {attempt}/{max_retries} for code={code}")

            had_response, response_hex = self._connect_and_send(steps)
            last_response = response_hex

            if response_hex:
                response_type = self.logger.analyze_response(response_hex)
                last_response_type = response_type

                if response_type == ServerResponse.ACK:
                    self.logger.info(f"Redemption successful: code={code}")
                    return {
                        "success": True,
                        "attempts": attempt,
                        "response": response_hex,
                        "response_type": response_type.name,
                        "error": None
                    }

                elif response_type == ServerResponse.REJECTED:
                    self.logger.warning(
                        f"Server rejected redemption (attempt {attempt}/{max_retries})"
                    )
                    # Don't retry on rejection — server won't accept this code
                    return {
                        "success": False,
                        "attempts": attempt,
                        "response": response_hex,
                        "response_type": response_type.name,
                        "error": "Server rejected the gift code"
                    }

                elif response_type == ServerResponse.RATE_LIMITED:
                    self.logger.warning(
                        f"Rate limited by server (attempt {attempt}/{max_retries})"
                    )
                    if attempt < max_retries:
                        self.logger.info(f"Waiting {delay:.1f}s before retry...")
                        time.sleep(delay)
                        delay = min(delay * 2, 120.0)
                    continue

                elif response_type == ServerResponse.TIMEOUT:
                    self.logger.warning(
                        f"Server timeout (attempt {attempt}/{max_retries})"
                    )
                    if attempt < max_retries:
                        self.logger.info(f"Waiting {delay:.1f}s before retry...")
                        time.sleep(delay)
                        delay = min(delay * 2, 120.0)
                    continue

            else:
                # No response at all
                self.logger.warning(f"No response (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    self.logger.info(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    delay = min(delay * 2, 120.0)

        # All retries exhausted
        self.logger.error(
            f"Redemption failed after {max_retries} attempts: "
            f"code={code}, last_response={last_response}, "
            f"last_response_type={last_response_type.name}"
        )
        return {
            "success": False,
            "attempts": max_retries,
            "response": last_response,
            "response_type": last_response_type.name,
            "error": f"All {max_retries} attempts failed"
        }

    def batch_redeem(self, codes: list[str]) -> dict[str, dict]:
        """
        Redeem multiple gift codes with randomized pauses.
        
        Returns:
            Dict mapping code -> result dict (same as redeem() return value)
        """
        results = {}
        total = len(codes)
        
        for i, code in enumerate(codes, 1):
            self.logger.info(f"\n{'='*40}\nBatch redeem [{i}/{total}]: {code}")
            
            result = self.redeem(code)
            results[code] = result
            
            if result["success"]:
                self.logger.info(f"Code {code}: SUCCESS (attempts={result['attempts']})")
            else:
                self.logger.warning(
                    f"Code {code}: FAILED — {result['error']} "
                    f"(attempts={result['attempts']}, type={result['response_type']})"
                )
            
            # Randomized cooldown between codes
            if i < total:
                pause = self.anti_detection.random_cycle_delay()
                self.logger.info(f"Pause between codes: {pause:.1f}s")
                time.sleep(pause)
        
        # Summary
        successful = sum(1 for r in results.values() if r["success"])
        self.logger.info(f"\nBatch complete: {successful}/{total} codes redeemed successfully")
        
        return results
