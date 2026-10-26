"""Release migration failure boundaries; never exercise production Docker."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def test_entrypoints_fail_closed_before_checkout_or_docker(tmp_path):
    for name, args in (("deploy.sh", ()), ("rollback.sh", ("a" * 40,))):
        result = subprocess.run(["bash", str(ROOT / "scripts" / name), *args],
                                cwd=tmp_path, capture_output=True, text=True,
                                env={**os.environ, "SAAS_EVENT_OPT_IN": "1"})
        assert result.returncode != 0
        assert "host integration" in result.stderr.lower()
        assert not list(tmp_path.iterdir())


def test_pending_gate_is_sticky_and_blocks_next_transition(tmp_path):
    from release_gate import ReleaseGate, PendingTransition
    gate = ReleaseGate(tmp_path)
    with gate.lock():
        gate.begin("deploy", "a" * 40, "b" * 64, True)
    assert json.loads((tmp_path / "pending.json").read_text())["old_id"] == "b" * 64
    with gate.lock():
        with pytest.raises(PendingTransition):
            gate.begin("rollback", "c" * 40, "d" * 64, False)


def test_finalize_refuses_without_host_proof_and_keeps_pending(tmp_path):
    from release_gate import ReleaseGate, IdentityMismatch, UnsafeState
    gate = ReleaseGate(tmp_path)
    with gate.lock():
        gate.begin("deploy", "a" * 40, "b" * 64, True)
        with pytest.raises(IdentityMismatch):
            gate.finish("c" * 64, "d" * 64)
        with pytest.raises(UnsafeState, match="host integration"):
            gate.finish("c" * 64, "b" * 64)
    assert (tmp_path / "pending.json").exists()
    assert not (tmp_path / "events.enabled").exists()


def test_symlinked_marker_fails_closed(tmp_path):
    from release_gate import ReleaseGate, UnsafeState
    (tmp_path / "events.enabled").symlink_to(tmp_path / "missing")
    with ReleaseGate(tmp_path).lock():
        with pytest.raises(UnsafeState):
            ReleaseGate(tmp_path).begin("deploy", "a" * 40, "b" * 64, False)


def test_lock_serializes_separate_processes(tmp_path):
    from release_gate import ReleaseGate, BusyRelease
    gate = ReleaseGate(tmp_path)
    with gate.lock():
        child = subprocess.run([sys.executable, str(ROOT / "scripts" / "release_gate.py"),
                                "probe", str(tmp_path)], capture_output=True, text=True)
        assert child.returncode == 2
        assert "busy" in child.stderr.lower()
    child = subprocess.run([sys.executable, str(ROOT / "scripts" / "release_gate.py"),
                            "probe", str(tmp_path)], capture_output=True, text=True)
    assert child.returncode == 0


def test_invalid_selection_and_pending_bytes_block_transition(tmp_path):
    from release_gate import ReleaseGate, UnsafeState
    (tmp_path / "events.enabled").write_bytes(b"enabled\nextra")
    with ReleaseGate(tmp_path).lock():
        with pytest.raises(UnsafeState):
            ReleaseGate(tmp_path).begin("deploy", "a" * 40, "b" * 64, False)
    (tmp_path / "events.enabled").unlink()
    (tmp_path / "pending.json").write_bytes(b"not json")
    with ReleaseGate(tmp_path).lock():
        with pytest.raises(UnsafeState):
            ReleaseGate(tmp_path).begin("deploy", "a" * 40, "b" * 64, False)


def test_replacement_identity_and_rollback_to_legacy_fail_closed(tmp_path):
    from release_gate import ReleaseGate, IdentityMismatch, UnsafeState
    gate = ReleaseGate(tmp_path)
    with gate.lock():
        gate.begin("deploy", "a" * 40, "b" * 64, True)
        with pytest.raises(IdentityMismatch):
            gate.finish("b" * 64, "b" * 64)
        with pytest.raises(UnsafeState, match="host integration"):
            gate.finish("c" * 64, "b" * 64)
    # Operator-installed selection, not created by the unavailable finalize hook.
    (tmp_path / "pending.json").unlink()
    (tmp_path / "events.enabled").write_bytes(b"enabled\n")
    (tmp_path / "events.enabled").chmod(0o600)
    with gate.lock():
        with pytest.raises(UnsafeState):
            gate.begin("rollback", "d" * 40, "c" * 64, False)


def test_symlinked_lock_is_rejected(tmp_path):
    from release_gate import ReleaseGate, UnsafeState
    (tmp_path / "release.lock").symlink_to(tmp_path / "outside")
    with pytest.raises(UnsafeState):
        with ReleaseGate(tmp_path).lock():
            pass


def test_pending_fsync_failure_never_allows_mutation(tmp_path, monkeypatch):
    import release_gate
    from release_gate import ReleaseGate
    gate = ReleaseGate(tmp_path)
    real_fsync = release_gate.os.fsync

    def fail_file_fsync(fd):
        if os.readlink(f"/proc/self/fd/{fd}").split("/")[-1].startswith(".release-"):
            raise OSError("simulated write failure")
        return real_fsync(fd)

    with gate.lock():
        monkeypatch.setattr(release_gate.os, "fsync", fail_file_fsync)
        with pytest.raises(OSError, match="simulated"):
            gate.begin("deploy", "a" * 40, "b" * 64, True)
    assert not (tmp_path / "pending.json").exists()
