"""
utils/logger.py — Centralized logging for Lords Mobile Bot
"""
import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class ServerResponse(Enum):
    """Known server response codes."""
    UNKNOWN = 0
    ACK = 1              # Server acknowledged the packet
    REJECTED = 2         # Server rejected (bad seq, invalid packet)
    TIMEOUT = 3          # No response within timeout window
    KICKED = 4           # Server kicked the session
    RATE_LIMITED = 5     # Server rate limiting
    BANNED = 6           # Account banned


# Server packet prefixes that indicate rejection (first 2 bytes after header)
REJECTION_PREFIXES = [
    "00",    # Generic empty/error
    "ffff",  # Error marker
]


class BotLogger:
    """
    Centralized logger with:
    - Console + file output
    - Structured JSON logs for machine parsing
    - Packet history ring buffer
    - Thread-safe
    - Configurable retention
    """
    
    _instance: Optional['BotLogger'] = None
    _lock = threading.Lock()

    def __init__(self, name: str = "lordsbot", log_dir: str = None):
        self.name = name
        self.log_dir = Path(log_dir or os.path.expanduser("~/.lordsbot/logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.packet_history: list[dict] = []
        self._history_lock = threading.Lock()
        self._max_history = 500  # Keep last 500 packets
        
        # Setup logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        ))
        self._logger.addHandler(ch)
        
        # File handler (rotating, 5MB per file, keep 5 files)
        fh = RotatingFileHandler(
            self.log_dir / f"{name}.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        self._logger.addHandler(fh)
        
        # JSON audit log (for packet analysis)
        self._audit_fh = RotatingFileHandler(
            self.log_dir / f"{name}_audit.json",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        self._audit_fh.setLevel(logging.DEBUG)
        self._audit_fh.setFormatter(logging.Formatter("%(message)s"))

    @classmethod
    def get(cls, name: str = "lordsbot") -> 'BotLogger':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(name)
        return cls._instance

    def _record_packet(self, direction: str, packet_hex: str, response_hex: str = None,
                       response_type: ServerResponse = None, metadata: dict = None):
        """Add packet to history ring buffer."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "direction": direction,  # "sent" or "received"
            "packet": packet_hex,
            "response": response_hex,
            "response_type": response_type.name if response_type else None,
            "metadata": metadata or {}
        }
        with self._history_lock:
            self.packet_history.append(entry)
            if len(self.packet_history) > self._max_history:
                self.packet_history.pop(0)
        
        # Also write to audit log
        self._logger.debug(
            f"PACKET {direction.upper()} {packet_hex[:40]}"
            + (f" -> {response_type.name}" if response_type else "")
        )

    # ─── Logging Methods ───────────────────────────────────────────────

    def debug(self, msg: str, **kwargs):
        self._logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._logger.critical(msg, **kwargs)

    # ─── Packet Logging ─────────────────────────────────────────────────

    def packet_sent(self, packet_hex: str, metadata: dict = None):
        """Log an outbound packet."""
        self._record_packet("sent", packet_hex, metadata=metadata)
        self.debug(f"→ SENT {packet_hex[:60]}{'...' if len(packet_hex) > 60 else ''}")

    def packet_received(self, packet_hex: str, response_type: ServerResponse = None,
                       metadata: dict = None):
        """Log an inbound packet."""
        self._record_packet("received", packet_hex, response_type=response_type, metadata=metadata)
        if response_type == ServerResponse.REJECTED:
            self.warning(f"← SERVER REJECTED: {packet_hex[:60]}")
        elif response_type == ServerResponse.KICKED:
            self.critical(f"← SERVER KICKED: {packet_hex[:80]}")
        elif response_type == ServerResponse.RATE_LIMITED:
            self.warning(f"← SERVER RATE LIMITED")
        elif response_type == ServerResponse.TIMEOUT:
            self.warning(f"← SERVER TIMEOUT (no response)")
        else:
            self.debug(f"← RECV {packet_hex[:60]}{'...' if len(packet_hex) > 60 else ''}")

    def analyze_response(self, response_hex: str) -> ServerResponse:
        """
        Analyze a server response and classify it.
        Returns ServerResponse enum value.
        """
        if not response_hex:
            return ServerResponse.TIMEOUT
        
        # Strip spaces
        hex_clean = response_hex.replace(" ", "").lower()
        
        # Empty or error prefixes
        if hex_clean.startswith("00") and len(hex_clean) < 8:
            return ServerResponse.REJECTED
        
        # Known rejection patterns (add more as discovered)
        rejection_patterns = [
            "ffff",  # Error marker
            "000000",  # Empty/nack
        ]
        for pattern in rejection_patterns:
            if hex_clean.startswith(pattern):
                return ServerResponse.REJECTED
        
        # Kick/ban patterns (heuristic — may need tuning)
        kick_patterns = [
            "4b49434b",  # "KICK"
            "42414e",    # "BAN"
        ]
        for pattern in kick_patterns:
            if pattern in hex_clean:
                return ServerResponse.BANNED
        
        # Rate limit patterns
        if "rate" in hex_clean or "cooldown" in hex_clean:
            return ServerResponse.RATE_LIMITED
        
        return ServerResponse.ACK

    # ─── Retry Logic ───────────────────────────────────────────────────

    def retry_with_backoff(self, func, *args,
                           max_retries: int = 5,
                           base_delay: float = 1.0,
                           max_delay: float = 60.0,
                           backoff_factor: float = 2.0,
                           on_retry: callable = None,
                           on_fail: callable = None,
                           **kwargs):
        """
        Execute a function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Arguments for func
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay cap in seconds
            backoff_factor: Multiplier for delay after each retry
            on_retry: Callback(response, attempt, delay) on each retry
            on_fail: Callback(exception) when all retries exhausted
            **kwargs: Keyword arguments for func
            
        Returns:
            Tuple (success: bool, result: any, attempts: int)
        """
        delay = base_delay
        last_response = None
        
        for attempt in range(1, max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Analyze the result
                if isinstance(result, (str, bytes)):
                    response_type = self.analyze_response(
                        result.hex() if isinstance(result, bytes) else result
                    )
                    last_response = result
                    
                    if response_type == ServerResponse.REJECTED:
                        self.warning(
                            f"Attempt {attempt}/{max_retries}: server rejected "
                            f"(delay={delay:.1f}s)"
                        )
                        if on_retry:
                            on_retry(result, attempt, delay)
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                        continue
                    
                    elif response_type == ServerResponse.RATE_LIMITED:
                        self.warning(
                            f"Attempt {attempt}/{max_retries}: rate limited "
                            f"(delay={delay:.1f}s)"
                        )
                        if on_retry:
                            on_retry(result, attempt, delay)
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                        continue
                    
                    elif response_type == ServerResponse.TIMEOUT:
                        self.warning(
                            f"Attempt {attempt}/{max_retries}: timeout "
                            f"(delay={delay:.1f}s)"
                        )
                        if on_retry:
                            on_retry(result, attempt, delay)
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                        continue
                
                # Success
                return True, result, attempt
                
            except Exception as e:
                self.error(f"Attempt {attempt}/{max_retries}: exception {type(e).__name__}: {e}")
                if attempt == max_retries:
                    if on_fail:
                        on_fail(e)
                    return False, e, attempt
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
        
        return False, last_response, max_retries

    # ─── Packet History ─────────────────────────────────────────────────

    def get_packet_history(self, limit: int = 50,
                           direction: str = None) -> list[dict]:
        """Get recent packet history."""
        with self._history_lock:
            hist = self.packet_history[-limit:]
            if direction:
                hist = [h for h in hist if h["direction"] == direction]
            return hist

    def get_failed_packets(self, limit: int = 20) -> list[dict]:
        """Get packets that received rejection/timeout."""
        with self._history_lock:
            return [
                h for h in self.packet_history
                if h.get("response_type") in ("REJECTED", "TIMEOUT", "RATE_LIMITED")
            ][-limit:]

    def export_history(self, path: str = None) -> str:
        """Export packet history as JSON file."""
        out_path = Path(path) if path else self.log_dir / f"packet_history_{datetime.now():%Y%m%d_%H%M%S}.json"
        with self._history_lock:
            with open(out_path, "w") as f:
                json.dump(self.packet_history, f, indent=2)
        return str(out_path)

    # ─── Convenience Shortcuts ──────────────────────────────────────────

    def attack_sent(self, zone: int, point: int, response_hex: str = None):
        """Log an attack march."""
        self._record_packet(
            "sent",
            f"attack:zone={zone}:point={point}",
            response_hex=response_hex,
            metadata={"type": "attack_march", "zone": zone, "point": point}
        )

    def attack_response(self, response_hex: str):
        """Log response to an attack."""
        rt = self.analyze_response(response_hex)
        self._record_packet("received", response_hex, response_type=rt)
        self.packet_received(response_hex, rt)

    def redeem_sent(self, code: str, response_hex: str = None):
        """Log a gift code redemption."""
        self._record_packet(
            "sent",
            f"redeem:{code}",
            response_hex=response_hex,
            metadata={"type": "gift_redeem", "code": code}
        )

    def redeem_response(self, response_hex: str):
        """Log response to a gift redemption."""
        rt = self.analyze_response(response_hex)
        self._record_packet("received", response_hex, response_type=rt)
        self.packet_received(response_hex, rt)


# Global shortcut
def get_logger(name: str = "lordsbot") -> BotLogger:
    return BotLogger.get(name)
