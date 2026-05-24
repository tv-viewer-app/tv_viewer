#!/usr/bin/env python3
"""L2 — Auto-triage helper for monitoring-labeled issues.

Reads an open GitHub issue (typically auto-filed by supabase-monitor.yml),
extracts an error signature from the body, queries Supabase via
``scripts/supabase_monitor.py triage_lookup`` for occurrence stats, dedups
against existing open issues with the same signature, assigns a severity
label, and posts an enriched triage comment.

Designed to be invoked from .github/workflows/triage-on-issue.yml on the
issues.opened event for issues labeled ``monitoring``.

Usage:
    GH_TOKEN=... SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \\
    python scripts/triage_issue.py --issue 42 --repo tv-viewer-app/tv_viewer

Exit codes:
    0  triage completed (labels + comment applied, or duplicate closed)
    2  CLI/environment error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Ensure utf-8 on Windows runners (CI is Linux but keep parity with monitor)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
MONITOR_SCRIPT = ROOT / "scripts" / "supabase_monitor.py"


# ---------------------------------------------------------------------------
# GitHub CLI helpers
# ---------------------------------------------------------------------------

def gh(*args: str, capture: bool = True) -> str:
    """Run ``gh`` CLI with the given arguments. Returns stdout."""
    cmd = ["gh", *args]
    res = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        sys.stderr.write(f"[gh failed] {' '.join(cmd)}\n{res.stderr}\n")
        sys.exit(2)
    return res.stdout.strip()


def get_issue(repo: str, number: int) -> dict:
    raw = gh(
        "issue",
        "view",
        str(number),
        "--repo",
        repo,
        "--json",
        "number,title,body,labels,state,createdAt",
    )
    return json.loads(raw)


def list_open_monitoring(repo: str) -> list[dict]:
    raw = gh(
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--label",
        "monitoring",
        "--limit",
        "200",
        "--json",
        "number,title,body,labels,createdAt",
    )
    return json.loads(raw)


def add_labels(repo: str, number: int, labels: list[str]) -> None:
    if not labels:
        return
    gh(
        "issue",
        "edit",
        str(number),
        "--repo",
        repo,
        *sum((["--add-label", lbl] for lbl in labels), []),
        capture=True,
    )


def post_comment(repo: str, number: int, body: str) -> None:
    # Use stdin via --body-file - to avoid shell quoting issues
    p = subprocess.run(
        ["gh", "issue", "comment", str(number), "--repo", repo, "--body-file", "-"],
        input=body,
        text=True,
        capture_output=True,
        check=False,
    )
    if p.returncode != 0:
        sys.stderr.write(f"[gh comment failed]\n{p.stderr}\n")
        sys.exit(2)


def close_issue(repo: str, number: int, reason: str) -> None:
    gh(
        "issue",
        "close",
        str(number),
        "--repo",
        repo,
        "--comment",
        reason,
        "--reason",
        "not planned",
    )


# ---------------------------------------------------------------------------
# Triage logic
# ---------------------------------------------------------------------------

# Error block in the issue body that supabase-monitor.yml fences with ``` ```
_FENCE_RE = re.compile(r"```\s*\n(.+?)\n```", re.DOTALL)

# Looks for "ERROR_TYPE: Message" lines inside the fence.
_ERR_LINE_RE = re.compile(r"^\s*([A-Z][A-Za-z0-9_]*Error\w*)\s*[:|]\s*(.+?)\s*$", re.MULTILINE)


def extract_search_token(body: str) -> str:
    """Pull a useful substring from the issue body to filter Supabase by.

    Strategy: find the first fenced code block (where supabase-monitor.yml
    dumps the error rows), look for an ``ErrorType: message`` line, and
    return ``ErrorType``. If nothing matches, return an empty string —
    the lookup will return the whole window, which is still informative.
    """
    fence_match = _FENCE_RE.search(body or "")
    chunk = fence_match.group(1) if fence_match else (body or "")
    err = _ERR_LINE_RE.search(chunk)
    if err:
        return err.group(1)
    return ""


def lookup_supabase(hours: int, match: str, limit: int) -> dict:
    """Invoke the existing supabase_monitor triage_lookup query."""
    cmd = [
        sys.executable,
        str(MONITOR_SCRIPT),
        "triage_lookup",
        "--hours",
        str(hours),
        "--limit",
        str(limit),
        "--version",
        match,  # the lookup query reuses --version as a substring filter
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        sys.stderr.write(f"[monitor failed]\n{res.stderr}\n")
        sys.exit(2)
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        sys.stderr.write(f"[monitor output not JSON]\n{res.stdout[:500]}\n")
        sys.exit(2)


def severity_for(count: int, hours: int) -> str:
    """Map 24h-equivalent occurrence count → severity label.

    The thresholds mirror what an on-call SOC analyst would do — a single
    occurrence is a P4 FYI, a regular drip is P3, dozens per day is P2,
    > 50/day is P1 wake-the-PM.
    """
    rate_24h = (count / max(hours, 1)) * 24
    if rate_24h >= 50:
        return "P1-critical"
    if rate_24h >= 10:
        return "P2-high"
    if rate_24h >= 2:
        return "P3-medium"
    return "P4-low"


def platform_labels(platforms: list[str]) -> list[str]:
    """Convert raw platform strings to canonical ``platform/*`` labels."""
    out: set[str] = set()
    for p in platforms or []:
        p = (p or "").strip().lower()
        if not p or p == "?":
            continue
        if p in ("web", "docker"):
            out.add("platform/web")
        elif p in ("android", "ios", "mobile"):
            out.add("platform/mobile")
        elif p in ("desktop", "windows", "linux", "mac", "darwin"):
            out.add("platform/desktop")
        else:
            out.add(f"platform/{p}")
    return sorted(out)


def find_duplicate(repo: str, sig: str, current_number: int) -> dict | None:
    """Look for an existing open monitoring issue carrying the same
    signature in a hidden ``<!-- sig: ... -->`` marker (added by this script
    on previous runs). Returns the duplicate dict or None.
    """
    marker = f"<!-- sig:{sig} -->"
    for issue in list_open_monitoring(repo):
        if issue["number"] == current_number:
            continue
        if marker in (issue.get("body") or ""):
            return issue
    return None


def render_comment(window_h: int, top: dict, sig: str, severity: str,
                   plat_labels: list[str]) -> str:
    sample = top.get("sample") or {}
    lines = [
        "## 🔍 Auto-triage",
        "",
        f"<!-- sig:{sig} -->",
        f"**Signature:** `{sig}`  ",
        f"**Severity:** `{severity}`  ",
        f"**Occurrences (last {window_h}h):** {top['count']}  ",
        f"**Unique devices:** {top['unique_devices']}  ",
        f"**Platforms:** {', '.join(top.get('platforms') or []) or '?'}  ",
        f"**Versions:** {', '.join(top.get('versions') or []) or '?'}  ",
        f"**First seen:** {top.get('first_seen')}  ",
        f"**Last seen:** {top.get('last_seen')}",
        "",
        "### Sample",
        "```",
        f"error_type:    {sample.get('error_type')}",
        f"context:       {sample.get('context')}",
        f"severity:      {sample.get('severity')}",
        f"error_message: {sample.get('error_message')}",
        f"stack_top:     {sample.get('stack_top')}",
        "```",
        "",
        "### Routing",
        "",
        f"Platform labels: {', '.join(plat_labels) or '_(none inferred)_'}",
        "",
        "_Triaged by [triage-on-issue.yml](../actions/workflows/triage-on-issue.yml). "
        "Next step: the sprint-planner workflow will rank this for the next "
        "sprint when the `triaged` label is applied._",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--issue", type=int, required=True, help="Issue number to triage")
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""),
                   help="owner/repo (defaults to GITHUB_REPOSITORY env)")
    p.add_argument("--hours", type=int, default=24, help="Lookup window")
    p.add_argument("--limit", type=int, default=500, help="Max event rows to scan")
    args = p.parse_args()

    if not args.repo:
        sys.stderr.write("--repo is required (or set GITHUB_REPOSITORY)\n")
        return 2

    issue = get_issue(args.repo, args.issue)
    body = issue.get("body") or ""
    token = extract_search_token(body)
    print(f"[triage] issue #{args.issue}: search token = {token!r}")

    data = lookup_supabase(args.hours, token, args.limit)
    sigs = data.get("signatures") or []
    if not sigs:
        # No matching events in window — likely a stale duplicate or a
        # client-only error that's already been resolved.
        post_comment(
            args.repo,
            args.issue,
            "## 🔍 Auto-triage\n\nNo matching events found in Supabase for "
            f"the last {args.hours}h. Marking as `triaged` with severity "
            "`P4-low`; close manually if this is no longer reproducing.",
        )
        add_labels(args.repo, args.issue, ["triaged", "P4-low"])
        return 0

    top = sigs[0]
    sig = top["signature"]

    dup = find_duplicate(args.repo, sig, args.issue)
    if dup:
        # Close as duplicate and bump occurrence count comment on the original.
        close_issue(
            args.repo,
            args.issue,
            f"Duplicate of #{dup['number']} — same signature `{sig}`. "
            "Closing automatically; aggregated counts will appear on the original.",
        )
        post_comment(
            args.repo,
            dup["number"],
            f"### 📈 Duplicate detected\n\nAnother monitoring alert for the "
            f"same signature `{sig}` arrived (#{args.issue}). "
            f"Window count is now {top['count']} occurrences across "
            f"{top['unique_devices']} unique devices.",
        )
        print(f"[triage] closed #{args.issue} as duplicate of #{dup['number']}")
        return 0

    severity = severity_for(top["count"], args.hours)
    plat_labels = platform_labels(top.get("platforms"))

    labels = ["triaged", severity] + plat_labels
    add_labels(args.repo, args.issue, labels)
    post_comment(
        args.repo,
        args.issue,
        render_comment(args.hours, top, sig, severity, plat_labels),
    )
    print(f"[triage] #{args.issue}: severity={severity}, labels={labels}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
