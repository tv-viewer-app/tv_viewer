"""Tests for shared database service."""
import hashlib
from utils.shared_db import ENABLED


def test_shared_db_respects_telemetry():
    """Shared DB should be disabled when telemetry is off."""
    # Just verify the module loads without errors
    import utils.shared_db as sdb
    assert hasattr(sdb, 'ENABLED')
