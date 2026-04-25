"""
Unit tests for the parental controls system (utils/parental.py).

Run with: pytest tests/test_parental.py -v
"""

import json
import os
import sys
import time

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parental import ParentalControls, _hash_pin, MAX_FAILED_ATTEMPTS, LOCKOUT_DURATION_SECONDS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_settings(tmp_path):
    """Return a path to a temporary parental_settings.json."""
    return str(tmp_path / "parental_settings.json")


@pytest.fixture
def pc(tmp_settings):
    """Fresh ParentalControls instance with an isolated settings file."""
    return ParentalControls(settings_path=tmp_settings)


# ---------------------------------------------------------------------------
# PIN hashing
# ---------------------------------------------------------------------------

class TestPinHashing:
    def test_hash_pin_returns_hex_string(self):
        h = _hash_pin("1234")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_hash_pin_deterministic(self):
        assert _hash_pin("0000") == _hash_pin("0000")

    def test_hash_pin_different_pins(self):
        assert _hash_pin("1234") != _hash_pin("5678")


# ---------------------------------------------------------------------------
# Initialisation & defaults
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_default_state(self, pc):
        assert pc.enabled is False
        assert pc.has_pin() is False
        assert pc.blocked_categories == []
        assert pc.is_over_18 is False

    def test_load_missing_file_keeps_defaults(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        ctrl = ParentalControls(settings_path=path)
        assert ctrl.enabled is False
        assert ctrl.has_pin() is False


# ---------------------------------------------------------------------------
# setup_pin / verify_pin
# ---------------------------------------------------------------------------

class TestPinSetupAndVerify:
    def test_setup_pin_enables_controls(self, pc):
        pc.setup_pin("1234")
        assert pc.enabled is True
        assert pc.has_pin() is True

    def test_verify_correct_pin(self, pc):
        pc.setup_pin("5678")
        assert pc.verify_pin("5678") is True

    def test_verify_wrong_pin(self, pc):
        pc.setup_pin("5678")
        assert pc.verify_pin("0000") is False

    def test_verify_without_pin_set(self, pc):
        assert pc.verify_pin("1234") is False

    def test_setup_pin_invalid_format_raises(self, pc):
        with pytest.raises(ValueError, match="4 digits"):
            pc.setup_pin("abc")
        with pytest.raises(ValueError, match="4 digits"):
            pc.setup_pin("12345")
        with pytest.raises(ValueError, match="4 digits"):
            pc.setup_pin("12")
        with pytest.raises(ValueError, match="4 digits"):
            pc.setup_pin("")

    def test_pin_stored_as_hash_not_plaintext(self, pc, tmp_settings):
        pc.setup_pin("9999")
        with open(tmp_settings, "r") as f:
            data = json.load(f)
        assert data["pin_hash"] != "9999"
        assert data["pin_hash"] == _hash_pin("9999")


# ---------------------------------------------------------------------------
# change_pin
# ---------------------------------------------------------------------------

class TestChangePin:
    def test_change_pin_success(self, pc):
        pc.setup_pin("1111")
        assert pc.change_pin("1111", "2222") is True
        assert pc.verify_pin("2222") is True
        assert pc.verify_pin("1111") is False

    def test_change_pin_wrong_old(self, pc):
        pc.setup_pin("1111")
        assert pc.change_pin("0000", "2222") is False
        # Old PIN still works
        assert pc.verify_pin("1111") is True

    def test_change_pin_invalid_new_format(self, pc):
        pc.setup_pin("1111")
        with pytest.raises(ValueError, match="4 digits"):
            pc.change_pin("1111", "abc")


# ---------------------------------------------------------------------------
# Lockout
# ---------------------------------------------------------------------------

class TestLockout:
    def test_lockout_after_max_attempts(self, pc):
        pc.setup_pin("1234")
        for _ in range(MAX_FAILED_ATTEMPTS):
            pc.verify_pin("0000")
        assert pc.is_locked_out() is True
        # Even correct PIN is rejected during lockout
        assert pc.verify_pin("1234") is False

    def test_lockout_remaining_positive(self, pc):
        pc.setup_pin("1234")
        for _ in range(MAX_FAILED_ATTEMPTS):
            pc.verify_pin("0000")
        assert pc.lockout_remaining() > 0
        assert pc.lockout_remaining() <= LOCKOUT_DURATION_SECONDS

    def test_lockout_expires(self, pc):
        pc.setup_pin("1234")
        for _ in range(MAX_FAILED_ATTEMPTS):
            pc.verify_pin("0000")
        # Manually expire the lockout
        pc._lockout_until = time.time() - 1
        assert pc.is_locked_out() is False
        assert pc.verify_pin("1234") is True

    def test_no_lockout_with_fewer_attempts(self, pc):
        pc.setup_pin("1234")
        for _ in range(MAX_FAILED_ATTEMPTS - 1):
            pc.verify_pin("0000")
        assert pc.is_locked_out() is False

    def test_lockout_remaining_zero_when_not_locked(self, pc):
        assert pc.lockout_remaining() == 0


# ---------------------------------------------------------------------------
# Channel blocking — categories
# ---------------------------------------------------------------------------

class TestCategoryBlocking:
    def test_no_block_when_disabled(self, pc):
        pc.blocked_categories = ["XXX", "Adult"]
        pc.enabled = False
        channel = {"name": "Test", "category": "XXX", "minimum_age": 0}
        assert pc.is_channel_blocked(channel) is False

    def test_block_matching_category(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["XXX", "Adult"])
        assert pc.is_channel_blocked({"category": "XXX"}) is True
        assert pc.is_channel_blocked({"category": "Adult"}) is True

    def test_category_case_insensitive(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["xxx"])
        assert pc.is_channel_blocked({"category": "XXX"}) is True
        assert pc.is_channel_blocked({"category": "Xxx"}) is True

    def test_non_blocked_category_passes(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["XXX"])
        assert pc.is_channel_blocked({"category": "News"}) is False

    def test_empty_category_not_blocked(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["XXX"])
        assert pc.is_channel_blocked({"category": ""}) is False
        assert pc.is_channel_blocked({}) is False


# ---------------------------------------------------------------------------
# Channel blocking — age rating
# ---------------------------------------------------------------------------

class TestOver18Blocking:
    def test_not_over_18_blocks_adult(self, pc):
        """When is_over_18=False, channels with adult categories are blocked."""
        pc.setup_pin("1234")
        pc.set_over_18(False)
        assert pc.is_channel_blocked({"category": "XXX"}) is True
        assert pc.is_channel_blocked({"category": "Adult"}) is True
        assert pc.is_channel_blocked({"category": "NSFW"}) is True

    def test_not_over_18_blocks_adult_case_insensitive(self, pc):
        """Adult keyword matching is case-insensitive."""
        pc.setup_pin("1234")
        pc.set_over_18(False)
        assert pc.is_channel_blocked({"category": "xxx"}) is True
        assert pc.is_channel_blocked({"category": "Xxx"}) is True
        assert pc.is_channel_blocked({"category": "ADULT"}) is True
        assert pc.is_channel_blocked({"category": "Nsfw"}) is True

    def test_not_over_18_allows_non_adult(self, pc):
        """Non-adult categories are not blocked by the over-18 check."""
        pc.setup_pin("1234")
        pc.set_over_18(False)
        assert pc.is_channel_blocked({"category": "News"}) is False
        assert pc.is_channel_blocked({"category": "Sports"}) is False

    def test_over_18_allows_adult(self, pc):
        """When is_over_18=True, adult channels are not blocked by the over-18 check."""
        pc.setup_pin("1234")
        pc.set_over_18(True)
        assert pc.is_channel_blocked({"category": "XXX"}) is False
        assert pc.is_channel_blocked({"category": "Adult"}) is False
        assert pc.is_channel_blocked({"category": "NSFW"}) is False

    def test_over_18_toggle(self, pc):
        """Toggling is_over_18 changes blocking behaviour."""
        pc.setup_pin("1234")
        pc.set_over_18(False)
        assert pc.is_channel_blocked({"category": "XXX"}) is True
        pc.set_over_18(True)
        assert pc.is_channel_blocked({"category": "XXX"}) is False

    def test_missing_category_not_blocked(self, pc):
        """Channels without a category are never blocked by the adult check."""
        pc.setup_pin("1234")
        pc.set_over_18(False)
        assert pc.is_channel_blocked({"category": ""}) is False
        assert pc.is_channel_blocked({}) is False


# ---------------------------------------------------------------------------
# Combined blocking
# ---------------------------------------------------------------------------

class TestCombinedBlocking:
    def test_both_category_block_and_over18(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["Sports"])
        pc.set_over_18(False)
        # Blocked by explicit category list
        assert pc.is_channel_blocked({"category": "Sports"}) is True
        # Blocked by adult keyword (user not over 18)
        assert pc.is_channel_blocked({"category": "XXX"}) is True
        # Neither
        assert pc.is_channel_blocked({"category": "News"}) is False

    def test_over18_does_not_override_category_block(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["Adult"])
        pc.set_over_18(True)
        # Still blocked by explicit category list even though user is 18+
        assert pc.is_channel_blocked({"category": "Adult"}) is True


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_with_correct_pin(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["XXX"])
        pc.set_over_18(True)
        assert pc.reset("1234") is True
        assert pc.enabled is False
        assert pc.has_pin() is False
        assert pc.blocked_categories == []
        assert pc.is_over_18 is False

    def test_reset_with_wrong_pin(self, pc):
        pc.setup_pin("1234")
        assert pc.reset("0000") is False
        assert pc.enabled is True


# ---------------------------------------------------------------------------
# Persistence (save / load)
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_and_load_round_trip(self, tmp_settings):
        pc1 = ParentalControls(settings_path=tmp_settings)
        pc1.setup_pin("4321")
        pc1.set_blocked_categories(["XXX", "Adult"])
        pc1.set_over_18(True)

        # Create a fresh instance from the same file
        pc2 = ParentalControls(settings_path=tmp_settings)
        assert pc2.enabled is True
        assert pc2.verify_pin("4321") is True
        assert set(pc2.blocked_categories) == {"XXX", "Adult"}
        assert pc2.is_over_18 is True

    def test_corrupted_file_keeps_defaults(self, tmp_settings):
        with open(tmp_settings, "w") as f:
            f.write("NOT VALID JSON {{{")
        pc = ParentalControls(settings_path=tmp_settings)
        assert pc.enabled is False
        assert pc.has_pin() is False

    def test_save_creates_file(self, tmp_settings):
        pc = ParentalControls(settings_path=tmp_settings)
        pc.setup_pin("1111")
        assert os.path.exists(tmp_settings)

    def test_json_structure(self, tmp_settings):
        pc = ParentalControls(settings_path=tmp_settings)
        pc.setup_pin("1234")
        pc.set_blocked_categories(["XXX"])
        pc.set_over_18(True)

        with open(tmp_settings, "r") as f:
            data = json.load(f)

        assert "enabled" in data
        assert "pin_hash" in data
        assert "blocked_categories" in data
        assert "is_over_18" in data
        assert data["enabled"] is True
        assert isinstance(data["blocked_categories"], list)
        assert data["is_over_18"] is True

    def test_backward_compat_min_age_18(self, tmp_settings):
        """Loading a legacy settings file with min_age >= 18 sets is_over_18=True."""
        legacy_data = {
            "enabled": True,
            "pin_hash": _hash_pin("1234"),
            "blocked_categories": [],
            "min_age": 18,
        }
        with open(tmp_settings, "w") as f:
            json.dump(legacy_data, f)

        pc = ParentalControls(settings_path=tmp_settings)
        assert pc.is_over_18 is True

    def test_backward_compat_min_age_below_18(self, tmp_settings):
        """Loading a legacy settings file with min_age < 18 sets is_over_18=False."""
        legacy_data = {
            "enabled": True,
            "pin_hash": _hash_pin("1234"),
            "blocked_categories": [],
            "min_age": 12,
        }
        with open(tmp_settings, "w") as f:
            json.dump(legacy_data, f)

        pc = ParentalControls(settings_path=tmp_settings)
        assert pc.is_over_18 is False


# ---------------------------------------------------------------------------
# Validate PIN format
# ---------------------------------------------------------------------------

class TestValidatePinFormat:
    @pytest.mark.parametrize("pin,expected", [
        ("1234", True),
        ("0000", True),
        ("9999", True),
        ("123", False),
        ("12345", False),
        ("abcd", False),
        ("12a4", False),
        ("", False),
        ("    ", False),
    ])
    def test_validate_pin_format(self, pin, expected):
        assert ParentalControls._validate_pin_format(pin) is expected


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_setup_pin_overwrites_previous(self, pc):
        pc.setup_pin("1111")
        pc.setup_pin("2222")
        assert pc.verify_pin("2222") is True
        assert pc.verify_pin("1111") is False

    def test_is_channel_blocked_with_none_category(self, pc):
        pc.setup_pin("1234")
        pc.set_blocked_categories(["XXX"])
        assert pc.is_channel_blocked({"category": None}) is False

    def test_is_channel_blocked_with_non_int_age(self, pc):
        pc.setup_pin("1234")
        pc.set_over_18(False)
        # Channel with string category that is not adult should not crash or block
        assert pc.is_channel_blocked({"category": "eighteen"}) is False

    def test_multiple_failed_then_success_resets_counter(self, pc):
        pc.setup_pin("1234")
        pc.verify_pin("0000")
        pc.verify_pin("0000")
        assert pc._failed_attempts == 2
        pc.verify_pin("1234")
        assert pc._failed_attempts == 0

    def test_lockout_clears_on_expiry_check(self, pc):
        pc.setup_pin("1234")
        for _ in range(MAX_FAILED_ATTEMPTS):
            pc.verify_pin("0000")
        assert pc.is_locked_out() is True
        pc._lockout_until = time.time() - 1
        assert pc.is_locked_out() is False
        assert pc._failed_attempts == 0
