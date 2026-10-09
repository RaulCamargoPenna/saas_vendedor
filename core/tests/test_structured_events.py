import json
import os
import time

import pytest

from core.structured_events import EventPublicationError, publish_event


def test_ready_publishes_a_private_bounded_closed_event(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    target = source / "events.jsonl"
    assert target.stat().st_mode & 0o777 == 0o600
    assert json.loads(target.read_text()) == {
        "version": 1, "timestamp": 1700000000, "code": "app.ready"
    }
    assert len(target.read_bytes().splitlines()) == 1


def test_rejects_untrusted_previous_file_without_clobbering(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    target.write_text("sensitive old contents")
    target.chmod(0o600)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready")
    assert target.read_text() == "sensitive old contents"


def test_job_success_requires_a_verified_job_hook(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    with pytest.raises(EventPublicationError, match="invalid event code"):
        publish_event(source, "job.succeeded")
    assert not (source / "events.jsonl").exists()


def test_duplicate_keys_in_previous_window_fail_closed(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    wire = b'{"version":1,"timestamp":1700000000,"code":"app.ready","code":"app.ready"}\n'
    target.write_bytes(wire)
    target.chmod(0o600)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    assert target.read_bytes() == wire


def test_older_event_time_cannot_replace_newer_window(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    target.write_bytes(b'{"version":1,"timestamp":1700000020,"code":"app.ready"}\n')
    target.chmod(0o600)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    assert json.loads(target.read_text())["timestamp"] == 1700000020
