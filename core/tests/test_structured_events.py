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


def test_short_previous_read_cannot_hide_invalid_later_line(tmp_path, monkeypatch):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    first = b'{"version":1,"timestamp":1700000000,"code":"app.ready"}\n'
    target.write_bytes(first + b'private-not-json\n')
    target.chmod(0o600)
    real_read = os.read
    calls = []

    def partial_read(fd, size):
        calls.append(size)
        return real_read(fd, len(first) if len(calls) == 1 else size)

    monkeypatch.setattr(os, "read", partial_read)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=1700000001, capture_ns=time.time_ns())
    assert target.read_bytes() == first + b'private-not-json\n'


def test_previous_open_is_nonblocking_and_rechecks_regular_file(tmp_path, monkeypatch):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    target.write_bytes(b'{"version":1,"timestamp":1700000000,"code":"app.ready"}\n')
    target.chmod(0o600)
    real_open = os.open

    def guarded_open(path, flags, *args, **kwargs):
        if path == "events.jsonl":
            assert flags & os.O_NONBLOCK, "a swapped FIFO could hang the probe"
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded_open)
    publish_event(source, "app.ready", now=1700000001, capture_ns=time.time_ns())


def test_previous_mutation_during_read_fails_closed(tmp_path, monkeypatch):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    wire = b'{"version":1,"timestamp":1700000000,"code":"app.ready"}\n'
    target.write_bytes(wire)
    target.chmod(0o600)
    real_read = os.read

    def mutating_read(fd, size):
        chunk = real_read(fd, size)
        with target.open("ab") as output:
            output.write(b"X")
        return chunk

    monkeypatch.setattr(os, "read", mutating_read)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=1700000001, capture_ns=time.time_ns())
    assert target.read_bytes() == wire + b"X"


def test_valid_previous_job_success_with_count_can_be_replaced(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    target.write_bytes(b'{"version":1,"timestamp":1700000000,"code":"job.succeeded","count":3}\n')
    target.chmod(0o600)
    publish_event(source, "app.ready", now=1700000001, capture_ns=time.time_ns())
    assert json.loads(target.read_text())["code"] == "app.ready"


def test_valid_future_previous_timestamp_is_not_misclassified(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    target.write_bytes(b'{"version":1,"timestamp":1700000030,"code":"app.ready"}\n')
    target.chmod(0o600)
    with pytest.raises(EventPublicationError, match="clock regression"):
        publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    assert json.loads(target.read_text())["timestamp"] == 1700000030


def test_negative_previous_timestamp_is_rejected_with_zero_clock(tmp_path):
    timestamp, now = -1, 0
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    wire = (json.dumps({"version": 1, "timestamp": timestamp, "code": "app.ready"}) + "\n").encode()
    target.write_bytes(wire)
    target.chmod(0o600)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=now, capture_ns=time.time_ns())
    assert target.read_bytes() == wire


def test_short_write_is_retried_before_atomic_publication(tmp_path, monkeypatch):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    real_write = os.write
    calls = []

    def short_write(fd, data):
        calls.append(len(data))
        return real_write(fd, data[:1] if len(calls) == 1 else data)

    monkeypatch.setattr(os, "write", short_write)
    publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    assert len(calls) > 1
    assert json.loads((source / "events.jsonl").read_text())["code"] == "app.ready"


def test_zero_byte_write_cannot_publish_partial_window(tmp_path, monkeypatch):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    monkeypatch.setattr(os, "write", lambda fd, data: 0)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    assert not (source / "events.jsonl").exists()


def test_cross_process_writers_leave_one_closed_window(tmp_path):
    import subprocess
    import sys
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    code = ("import sys,time; from core.structured_events import publish_event,EventPublicationError; "
            "\ntry: publish_event(sys.argv[1], 'app.ready', now=int(time.time()), "
            "capture_ns=time.time_ns())\nexcept EventPublicationError: pass")
    children = [subprocess.Popen([sys.executable, "-c", code, str(source)]) for _ in range(8)]
    assert all(child.wait(timeout=10) == 0 for child in children)
    wire = (source / "events.jsonl").read_bytes()
    assert wire.endswith(b"\n") and len(wire.splitlines()) == 1
    assert json.loads(wire)["code"] == "app.ready"
    assert not list(source.glob(".events-*"))


def test_older_event_time_cannot_replace_newer_window(tmp_path):
    source = tmp_path / "producer"
    source.mkdir(mode=0o700)
    target = source / "events.jsonl"
    target.write_bytes(b'{"version":1,"timestamp":1700000020,"code":"app.ready"}\n')
    target.chmod(0o600)
    with pytest.raises(EventPublicationError):
        publish_event(source, "app.ready", now=1700000000, capture_ns=time.time_ns())
    assert json.loads(target.read_text())["timestamp"] == 1700000020
