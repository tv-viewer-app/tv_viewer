"""Parental controls system for TV Viewer application.

Provides PIN-based locking, category blocking, and age-rating filtering
to restrict access to inappropriate channels.

Settings are persisted to parental_settings.json in config.BASE_DIR.
"""

import hashlib
import json
import os
import time
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

try:
    import config
    _SETTINGS_FILE = os.path.join(config.BASE_DIR, "parental_settings.json")
except ImportError:
    _SETTINGS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "parental_settings.json",
    )

# Lockout configuration
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION_SECONDS = 30


def _hash_pin(pin: str) -> str:
    """Return the SHA-256 hex digest of *pin*."""
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


class ParentalControls:
    """PIN-protected parental-control system.

    Attributes:
        enabled:              Whether parental controls are active.
        blocked_categories:   Category names whose channels are hidden.
        is_over_18:           When ``False``, channels with adult categories are blocked.
    """

    # Category keywords that indicate adult content (case-insensitive)
    _ADULT_CATEGORY_KEYWORDS = {'xxx', 'adult', 'nsfw'}

    def __init__(self, settings_path: Optional[str] = None):
        self._settings_path = settings_path or _SETTINGS_FILE
        self.enabled: bool = False
        self._pin_hash: Optional[str] = None
        self.blocked_categories: List[str] = []
        self.is_over_18: bool = False

        # Lockout state (not persisted)
        self._failed_attempts: int = 0
        self._lockout_until: float = 0.0

        self.load()

    # ------------------------------------------------------------------
    # PIN management
    # ------------------------------------------------------------------

    def setup_pin(self, pin: str) -> None:
        """Hash *pin* with SHA-256, store it, enable controls, and persist."""
        if not self._validate_pin_format(pin):
            raise ValueError("PIN must be exactly 4 digits")
        self._pin_hash = _hash_pin(pin)
        self.enabled = True
        self.save()
        logger.info("Parental controls PIN set and controls enabled")

    def verify_pin(self, pin: str) -> bool:
        """Check *pin* against the stored hash.

        Returns ``False`` when the account is locked out, even if the PIN
        is correct.  Resets the attempt counter on success.
        """
        if self.is_locked_out():
            remaining = int(self._lockout_until - time.time())
            logger.warning("PIN verification blocked — lockout active (%ds remaining)", remaining)
            return False

        if self._pin_hash is None:
            return False

        if _hash_pin(pin) == self._pin_hash:
            self._failed_attempts = 0
            return True

        self._failed_attempts += 1
        logger.warning("Invalid PIN attempt %d/%d", self._failed_attempts, MAX_FAILED_ATTEMPTS)

        if self._failed_attempts >= MAX_FAILED_ATTEMPTS:
            self._lockout_until = time.time() + LOCKOUT_DURATION_SECONDS
            logger.warning("Max PIN attempts reached — lockout for %ds", LOCKOUT_DURATION_SECONDS)

        return False

    def change_pin(self, old_pin: str, new_pin: str) -> bool:
        """Verify *old_pin* then set *new_pin*.  Returns success status."""
        if not self.verify_pin(old_pin):
            return False
        if not self._validate_pin_format(new_pin):
            raise ValueError("PIN must be exactly 4 digits")
        self._pin_hash = _hash_pin(new_pin)
        self.save()
        logger.info("Parental controls PIN changed")
        return True

    def has_pin(self) -> bool:
        """Return ``True`` when a PIN hash has been stored."""
        return self._pin_hash is not None

    def is_locked_out(self) -> bool:
        """Return ``True`` when too many wrong attempts have triggered a lockout."""
        if self._failed_attempts >= MAX_FAILED_ATTEMPTS and time.time() < self._lockout_until:
            return True
        # Auto-clear expired lockout
        if self._lockout_until and time.time() >= self._lockout_until:
            self._failed_attempts = 0
            self._lockout_until = 0.0
        return False

    def lockout_remaining(self) -> int:
        """Seconds remaining on the current lockout (0 if not locked out)."""
        if self.is_locked_out():
            return max(0, int(self._lockout_until - time.time()))
        return 0

    # ------------------------------------------------------------------
    # Channel filtering
    # ------------------------------------------------------------------

    def is_channel_blocked(self, channel: dict) -> bool:
        """Return ``True`` if *channel* should be hidden.

        A channel is blocked when **any** of the following apply
        (and parental controls are enabled):

        1. Its ``category`` is in :attr:`blocked_categories` (case-insensitive).
        2. The user has **not** confirmed they are 18+ and the channel's
           category matches an adult keyword (``xxx``, ``adult``, ``nsfw``).
        """
        if not self.enabled:
            return False

        # Category check (case-insensitive)
        cat = (channel.get("category") or "").strip().lower()

        if self.blocked_categories:
            if cat and cat in {c.lower() for c in self.blocked_categories}:
                return True

        # Adult-content check: block if user is NOT over 18
        if not self.is_over_18 and cat:
            if any(kw in cat for kw in self._ADULT_CATEGORY_KEYWORDS):
                return True

        return False

    def set_blocked_categories(self, categories: List[str]) -> None:
        """Replace the blocked-category list and persist."""
        self.blocked_categories = list(categories)
        self.save()
        logger.info("Blocked categories updated: %s", self.blocked_categories)

    def set_over_18(self, value: bool) -> None:
        """Set the over-18 confirmation flag and persist."""
        self.is_over_18 = bool(value)
        self.save()
        logger.info("Over-18 flag set to %s", self.is_over_18)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, pin: str) -> bool:
        """Verify *pin* then disable all parental controls."""
        if not self.verify_pin(pin):
            return False
        self.enabled = False
        self._pin_hash = None
        self.blocked_categories = []
        self.is_over_18 = False
        self._failed_attempts = 0
        self._lockout_until = 0.0
        self.save()
        logger.info("Parental controls have been reset")
        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist current settings to JSON on disk."""
        data = {
            "enabled": self.enabled,
            "pin_hash": self._pin_hash,
            "blocked_categories": self.blocked_categories,
            "is_over_18": self.is_over_18,
        }
        try:
            with open(self._settings_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            logger.debug("Parental settings saved to %s", self._settings_path)
        except Exception as exc:
            logger.error("Failed to save parental settings: %s", exc)

    def load(self) -> None:
        """Load settings from the JSON file (silently keeps defaults on error)."""
        if not os.path.exists(self._settings_path):
            return
        try:
            with open(self._settings_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.enabled = bool(data.get("enabled", False))
            self._pin_hash = data.get("pin_hash")
            self.blocked_categories = list(data.get("blocked_categories", []))

            # New key — preferred
            if "is_over_18" in data:
                self.is_over_18 = bool(data["is_over_18"])
            # Backward compat: migrate legacy min_age setting
            elif "min_age" in data:
                self.is_over_18 = int(data["min_age"]) >= 18
            else:
                self.is_over_18 = False

            logger.info(
                "Parental settings loaded (enabled=%s, categories=%d, is_over_18=%s)",
                self.enabled,
                len(self.blocked_categories),
                self.is_over_18,
            )
        except Exception as exc:
            logger.error("Failed to load parental settings: %s", exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_pin_format(pin: str) -> bool:
        """Return ``True`` if *pin* is exactly 4 digits."""
        return isinstance(pin, str) and len(pin) == 4 and pin.isdigit()
