"""Centralised first-launch consent storage (Issue #170).

Stores three boolean opt-ins under ``~/.tv_viewer/consent.json``:

    - analytics:   anonymous usage stats / Supabase telemetry
    - online_db:   fetch crowdsourced channel database from network
    - geo_ip:      use IP geolocation to pin the local channel row

All defaults are ``False``.  The dialog re-prompts on POLICY_VERSION bumps.
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, Any

POLICY_VERSION = 1  # Bump to re-prompt every user

_DEFAULTS: Dict[str, bool] = {
    "analytics": False,
    "online_db": False,
    "geo_ip": False,
}


def _consent_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".tv_viewer")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "consent.json")


def load_consent() -> Dict[str, Any]:
    """Load consent from disk.  Returns dict with `_DEFAULTS` keys + meta."""
    path = _consent_path()
    if not os.path.exists(path):
        return {**_DEFAULTS, "policy_version": 0, "answered": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {**_DEFAULTS, "policy_version": 0, "answered": False}

    out = {**_DEFAULTS}
    for k in _DEFAULTS:
        if isinstance(data.get(k), bool):
            out[k] = data[k]
    out["policy_version"] = int(data.get("policy_version", 0))
    out["answered"] = bool(data.get("answered", False))
    return out


def save_consent(values: Dict[str, bool]) -> None:
    """Persist consent values plus current policy version + timestamp."""
    payload: Dict[str, Any] = {k: bool(values.get(k, False)) for k in _DEFAULTS}
    payload["policy_version"] = POLICY_VERSION
    payload["answered"] = True
    payload["timestamp"] = time.time()
    try:
        with open(_consent_path(), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


def needs_prompt() -> bool:
    """True if first-launch dialog should be shown."""
    data = load_consent()
    if not data.get("answered"):
        return True
    return int(data.get("policy_version", 0)) < POLICY_VERSION


def apply_to_config(values: Dict[str, bool]) -> None:
    """Mirror consent into the global ``config`` module so other code reads it."""
    try:
        import config
        config.TELEMETRY_ENABLED = bool(values.get("analytics", False))
        config.ONLINE_DB_ENABLED = bool(values.get("online_db", False))
        config.GEO_IP_ENABLED = bool(values.get("geo_ip", False))
    except Exception:
        pass
