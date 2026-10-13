from unittest.mock import Mock

import pytest
import requests

from scripts import analytics_dashboard as dashboard


def response(rows):
    result = Mock()
    result.json.return_value = rows
    return result


def test_query_paginates_server_capped_pages(monkeypatch):
    pages = iter([response([{"id": 1}]), response([{"id": 2}]), response([])])
    calls = []

    def get(url, **kwargs):
        calls.append(kwargs["params"])
        return next(pages)

    monkeypatch.setattr(dashboard.requests, "get", get)
    monkeypatch.setattr(dashboard, "_TIME_FILTER", "&created_at=gte.2026-10-01")
    assert dashboard._query("select=id", limit=10) == [{"id": 1}, {"id": 2}]
    assert [dict(call)["offset"] for call in calls] == ["0", "1", "2"]
    assert all(dict(call)["created_at"] == "gte.2026-10-01" for call in calls)


def test_query_propagates_http_failure(monkeypatch):
    failed = response([])
    failed.raise_for_status.side_effect = requests.HTTPError("unavailable")
    monkeypatch.setattr(dashboard.requests, "get", lambda *a, **k: failed)
    with pytest.raises(requests.HTTPError):
        dashboard._query("select=id")


def test_performance_uses_supported_query_and_reports_latency(monkeypatch, capsys):
    query = Mock(return_value=[
        {"event_data": {"metric": "stream_to_first_frame", "duration_ms": 1200}},
    ])
    monkeypatch.setattr(dashboard, "_query", query)
    dashboard.show_performance()
    query.assert_called_once_with(
        "select=event_data&event_type=eq.perf_metric&order=created_at.desc,id.desc",
        limit=50000,
    )
    assert "1200ms" in capsys.readouterr().out


def test_count_propagates_http_failure(monkeypatch):
    failed = response([])
    failed.raise_for_status.side_effect = requests.HTTPError("unauthorized")
    monkeypatch.setattr(dashboard.requests, "get", lambda *a, **k: failed)
    with pytest.raises(requests.HTTPError):
        dashboard._query_count("select=id")


def test_channel_failures_reported_without_crashes(monkeypatch, capsys):
    query = Mock(side_effect=[
        [],
        [{"event_data": {"error_code": "network_timeout"}}],
    ])
    monkeypatch.setattr(dashboard, "_query", query)
    dashboard.show_crashes()
    output = capsys.readouterr().out
    assert "No crashes recorded" in output
    assert "network_timeout" in output
    assert query.call_count == 2


def test_performance_includes_recent_events_beyond_old_cap(monkeypatch, capsys):
    events = [
        {"event_data": {"metric": "stream_to_first_frame", "duration_ms": 9000}}
        for _ in range(501)
    ]
    monkeypatch.setattr(dashboard, "_query", Mock(return_value=events))
    dashboard.show_performance()
    output = capsys.readouterr().out
    assert "Samples: 501" in output
    assert "REGRESSION" in output
