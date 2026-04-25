"""Tests for thumbnail utility."""
import os
import hashlib
from utils.thumbnail import get_thumbnail_path, thumbnail_exists


def test_get_thumbnail_path():
    path = get_thumbnail_path("http://example.com/stream.m3u8")
    assert path.endswith(".png")
    assert os.path.dirname(path)  # Has a directory component


def test_different_urls_different_paths():
    path1 = get_thumbnail_path("http://example.com/stream1.m3u8")
    path2 = get_thumbnail_path("http://example.com/stream2.m3u8")
    assert path1 != path2


def test_same_url_same_path():
    path1 = get_thumbnail_path("http://example.com/stream.m3u8")
    path2 = get_thumbnail_path("http://example.com/stream.m3u8")
    assert path1 == path2
