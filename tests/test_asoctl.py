from __future__ import annotations

import json

import asoctl


def test_status_reports_backup_count(tmp_path, capsys):
    state_dir = tmp_path / "runtime" / "state"
    backup_dir = state_dir / "backups"
    backup_dir.mkdir(parents=True)
    (backup_dir / "project_memory_20260101T000000Z.sqlite").write_bytes(b"backup")

    control = asoctl.ASOControl(state_dir=state_dir)

    assert control.status() == 0

    output = capsys.readouterr().out
    assert "ASO-X local state" in output
    assert "backup_count=1" in output
    assert "latest_backup=" in output


def test_autopilot_status_route(monkeypatch):
    called = {"value": False}

    def fake_autopilot_status(self):
        called["value"] = True
        return 0

    monkeypatch.setattr(asoctl.ASOControl, "autopilot_status", fake_autopilot_status)

    assert asoctl.main(["autopilot-status"]) == 0
    assert called["value"] is True


def test_autopilot_status_prints_json(monkeypatch, capsys):
    payload = {
        "schema_version": "aso-x.autopilot_readiness.v1",
        "status": "not_ready",
    }

    def fake_collect_autopilot_status(repo_root):
        return payload

    import tools.autopilot_status as autopilot_status

    monkeypatch.setattr(
        autopilot_status,
        "collect_autopilot_status",
        fake_collect_autopilot_status,
    )

    control = asoctl.ASOControl()

    assert control.autopilot_status() == 0

    parsed = json.loads(capsys.readouterr().out)
    assert parsed == payload
