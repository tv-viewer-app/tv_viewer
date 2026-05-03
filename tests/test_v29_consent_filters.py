"""Tests for v2.9 consent + filter modules."""
from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

import pytest


def _isolate_home(monkeypatch, tmp_path):
    """Redirect ~/.tv_viewer to a tmp dir."""
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    # Force expanduser to use the new home
    monkeypatch.setattr(os.path, "expanduser",
                        lambda p: p.replace("~", str(tmp_path)))


# -------------------- consent --------------------

def test_consent_defaults_when_missing(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from utils import consent
    data = consent.load_consent()
    assert data["analytics"] is False
    assert data["online_db"] is False
    assert data["geo_ip"] is False
    assert data["answered"] is False
    assert consent.needs_prompt() is True


def test_consent_save_and_reload(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from utils import consent
    consent.save_consent({"analytics": True, "online_db": False, "geo_ip": True})
    data = consent.load_consent()
    assert data["analytics"] is True
    assert data["online_db"] is False
    assert data["geo_ip"] is True
    assert data["answered"] is True
    assert consent.needs_prompt() is False


def test_consent_corrupt_file(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from utils import consent
    path = consent._consent_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write("{this is not json")
    data = consent.load_consent()
    assert data["analytics"] is False
    assert data["answered"] is False


def test_consent_policy_version_bump_reprompts(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from utils import consent
    consent.save_consent({"analytics": True})
    assert consent.needs_prompt() is False
    monkeypatch.setattr(consent, "POLICY_VERSION",
                        consent.POLICY_VERSION + 1)
    assert consent.needs_prompt() is True


def test_apply_to_config_mirrors_flags(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    import config
    from utils import consent
    consent.apply_to_config({"analytics": True, "online_db": True, "geo_ip": False})
    assert config.TELEMETRY_ENABLED is True
    assert config.ONLINE_DB_ENABLED is True
    assert config.GEO_IP_ENABLED is False


# -------------------- filters --------------------

def test_filter_passes_when_no_filters_active():
    from ui.filter_dialog import channel_passes
    ch = {"language": "English", "country": "US", "category": "News"}
    assert channel_passes(ch, {"language": set(), "country": set(), "category": set()})


def test_filter_excludes_non_matching_country():
    from ui.filter_dialog import channel_passes
    ch = {"language": "English", "country": "US", "category": "News"}
    assert not channel_passes(
        ch, {"language": set(), "country": {"UK"}, "category": set()})


def test_filter_includes_matching_country():
    from ui.filter_dialog import channel_passes
    ch = {"country": "US", "category": "News"}
    assert channel_passes(
        ch, {"language": set(), "country": {"US", "UK"}, "category": set()})


def test_filter_and_across_dimensions():
    from ui.filter_dialog import channel_passes
    ch = {"language": "English", "country": "US", "category": "Sports"}
    # Country matches, but category doesn't → excluded
    assert not channel_passes(
        ch, {"language": set(), "country": {"US"}, "category": {"News"}})


def test_filter_unknown_country_passes_country_filter():
    """Channels without a country tag aren't excluded by a country filter."""
    from ui.filter_dialog import channel_passes
    ch = {"category": "News"}  # no country
    assert channel_passes(
        ch, {"language": set(), "country": {"US"}, "category": set()})


def test_filter_save_load_roundtrip(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from ui.filter_dialog import save_filters, load_filters
    save_filters({"language": ["English"], "country": ["US", "UK"], "category": []})
    loaded = load_filters()
    assert loaded["language"] == {"English"}
    assert loaded["country"] == {"US", "UK"}
    assert loaded["category"] == set()


# -------------------- tour --------------------

def test_tour_marks_shown(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from ui.tour_overlay import tour_already_shown, mark_tour_shown
    assert tour_already_shown() is False
    mark_tour_shown()
    assert tour_already_shown() is True
