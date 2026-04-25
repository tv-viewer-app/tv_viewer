"""Tests for telemetry module."""


def test_telemetry_import():
    """Telemetry module should import without errors."""
    import utils.telemetry as tel
    assert hasattr(tel, 'is_configured')
    assert hasattr(tel, 'track_channel_play')


def test_hash_function():
    """Hash function should produce consistent SHA-256 hashes."""
    from utils.telemetry import _hash
    h1 = _hash("test_value")
    h2 = _hash("test_value")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex length
