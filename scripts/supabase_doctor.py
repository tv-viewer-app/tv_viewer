#!/usr/bin/env python3
"""Supabase schema doctor — verifies v2.16.0 migration is applied.

Reads SUPABASE_URL / SUPABASE_ANON_KEY from env (or config.py if importable),
then performs the following checks against the live database:

  1. channel_votes table exists and is readable.
  2. RPCs report_channel_broken, report_channel_working,
     promote_channel_source, tv_viewer_schema_version are callable.
  3. Schema version reports '2.16.0'.

Exit code:
  0 — all checks passed
  1 — one or more checks failed (prints remediation instructions)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Tuple

try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config as _cfg
    SUPABASE_URL = getattr(_cfg, 'SUPABASE_URL', '') or os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY = getattr(_cfg, 'SUPABASE_ANON_KEY', '') or os.environ.get('SUPABASE_ANON_KEY', '')
except Exception:
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')


GREEN = '\033[92m'
RED   = '\033[91m'
YEL   = '\033[93m'
RESET = '\033[0m'


def _ok(msg: str) -> None:
    print(f'{GREEN}✓{RESET} {msg}')


def _fail(msg: str) -> None:
    print(f'{RED}✗{RESET} {msg}')


def _warn(msg: str) -> None:
    print(f'{YEL}!{RESET} {msg}')


def _request(method: str, path: str, body: dict | None = None) -> Tuple[int, str]:
    url = f'{SUPABASE_URL}{path}'
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return 0, str(e)


def check_table_channel_votes() -> bool:
    # Query only columns explicitly granted to anon (url_hash, vote, created_at).
    # `id` and `device_id` are intentionally NOT granted — querying them
    # would return 401 by design, which is correct security behavior.
    status, body = _request('GET', '/rest/v1/channel_votes?select=url_hash&limit=1')
    if status == 200:
        _ok('Table channel_votes exists and is readable')
        return True
    _fail(f'Table channel_votes check failed (HTTP {status}): {body[:160]}')
    return False


def check_rpc(name: str, payload: dict, expect_ok_field: bool = True) -> bool:
    status, body = _request('POST', f'/rest/v1/rpc/{name}', body=payload)
    if status not in (200, 204):
        _fail(f'RPC {name} HTTP {status}: {body[:200]}')
        return False
    if status == 204 or not body.strip():
        _ok(f'RPC {name} callable')
        return True
    try:
        parsed = json.loads(body)
    except Exception:
        _ok(f'RPC {name} callable (non-JSON response)')
        return True
    if expect_ok_field:
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if isinstance(parsed, dict) and 'ok' in parsed:
            _ok(f'RPC {name} callable (ok={parsed.get("ok")})')
            return True
    _ok(f'RPC {name} callable')
    return True


def check_schema_version() -> bool:
    status, body = _request('POST', '/rest/v1/rpc/tv_viewer_schema_version', body={})
    if status not in (200, 204):
        _fail(f'Schema version RPC HTTP {status}: {body[:160]}')
        return False
    try:
        version = json.loads(body)
        if isinstance(version, list) and version:
            version = version[0]
        if isinstance(version, dict):
            version = next(iter(version.values()), None)
    except Exception:
        version = body.strip().strip('"')
    if version == '2.16.0':
        _ok(f'Schema version = {version}')
        return True
    _fail(f'Schema version mismatch (got {version!r}, expected 2.16.0)')
    return False


def print_remediation() -> None:
    print()
    print(f'{YEL}━━ Remediation ━━{RESET}')
    print('  1. Open the Supabase SQL editor for your project.')
    print('  2. Paste & run scripts/supabase_setup.sql (if never run).')
    print('  3. Paste & run scripts/supabase_security_hardening.sql.')
    print('  4. Paste & run scripts/supabase_migration_v2.16.0.sql.')
    print('  5. Re-run: python scripts/supabase_doctor.py')


def main() -> int:
    print('TV Viewer — Supabase doctor (v2.16.0)')
    print(f'URL: {SUPABASE_URL or "(not set)"}')
    print('─' * 50)

    if not SUPABASE_URL or not SUPABASE_KEY:
        _fail('SUPABASE_URL / SUPABASE_ANON_KEY not configured')
        print('  Export env vars or set them in config.py')
        return 1

    results = []
    results.append(check_table_channel_votes())
    # Dummy hash & device that satisfy length checks but won't match real data.
    dummy_hash = 'd' * 64
    dummy_dev = 'doctor-probe-0000-0000-0000-000000000000'
    results.append(check_rpc('report_channel_broken',
                             {'p_url_hash': dummy_hash, 'p_device_id': dummy_dev}))
    results.append(check_rpc('report_channel_working',
                             {'p_url_hash': dummy_hash, 'p_device_id': dummy_dev}))
    results.append(check_rpc('promote_channel_source',
                             {'p_channel_name': '__doctor_probe__',
                              'p_working_url': 'http://example.invalid/x',
                              'p_working_hash': dummy_hash}))
    results.append(check_schema_version())

    print('─' * 50)
    if all(results):
        print(f'{GREEN}All checks passed — schema is healthy.{RESET}')
        return 0

    print(f'{RED}One or more checks failed.{RESET}')
    print_remediation()
    return 1


if __name__ == '__main__':
    sys.exit(main())
