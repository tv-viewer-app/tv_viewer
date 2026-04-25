"""Tests for FavoritesManager."""
import json
import os
import tempfile
import pytest
from utils.favorites import FavoritesManager


@pytest.fixture
def fav_manager(tmp_path):
    """Create a FavoritesManager with a temp file."""
    filepath = str(tmp_path / "favorites.json")
    return FavoritesManager(filepath=filepath)


def test_add_favorite(fav_manager):
    fav_manager.add_favorite("http://stream1.example.com")
    assert fav_manager.is_favorite("http://stream1.example.com")
    assert fav_manager.get_favorite_count() == 1


def test_remove_favorite(fav_manager):
    fav_manager.add_favorite("http://stream1.example.com")
    fav_manager.remove_favorite("http://stream1.example.com")
    assert not fav_manager.is_favorite("http://stream1.example.com")


def test_toggle_favorite(fav_manager):
    result = fav_manager.toggle_favorite("http://stream1.example.com")
    assert result is True
    result = fav_manager.toggle_favorite("http://stream1.example.com")
    assert result is False


def test_persistence(tmp_path):
    filepath = str(tmp_path / "favorites.json")
    mgr1 = FavoritesManager(filepath=filepath)
    mgr1.add_favorite("http://stream1.example.com")
    mgr1.add_to_recent("http://stream1.example.com", "Stream 1")

    mgr2 = FavoritesManager(filepath=filepath)
    assert mgr2.is_favorite("http://stream1.example.com")
    assert len(mgr2.get_recent()) == 1


def test_recent_limit(fav_manager):
    for i in range(25):
        fav_manager.add_to_recent(f"http://stream{i}.example.com", f"Stream {i}")
    assert len(fav_manager.get_recent(limit=100)) <= 20  # MAX_RECENT


def test_corrupted_file(tmp_path):
    filepath = str(tmp_path / "favorites.json")
    with open(filepath, 'w') as f:
        f.write("not valid json{{{")
    mgr = FavoritesManager(filepath=filepath)
    assert mgr.get_favorite_count() == 0  # Should recover gracefully
