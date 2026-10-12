#!/usr/bin/env python3
"""Offline release transition primitive; NOT a production release entrypoint.

The host collector has no installed SaaS-specific prepare/finalize integration yet.
The public entrypoints therefore refuse *all* releases rather than mutating Docker.
Only a future reviewed adapter may call begin while holding the same lock;
finish is deliberately disabled until host proofs exist.
"""
import contextlib
import errno
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


class UnsafeState(RuntimeError):
    pass


class PendingTransition(UnsafeState):
    pass


class IdentityMismatch(UnsafeState):
    pass


class BusyRelease(UnsafeState):
    pass


HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ReleaseGate:
    def __init__(self, state_dir):
        self.directory = Path(state_dir)
        self._locked = False

    def _dirfd(self):
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        metadata = os.fstat(fd)
        if metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077:
            os.close(fd)
            raise UnsafeState("state directory must be private and owned by release operator")
        return fd

    def _read(self, name):
        fd = self._dirfd()
        try:
            try:
                item = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            except FileNotFoundError:
                return None
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise UnsafeState("symlinked release state") from None
                raise
            try:
                st = os.fstat(item)
                if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.geteuid() or st.st_mode & 0o077 or st.st_size > 512:
                    raise UnsafeState("unsafe release state")
                data = os.read(item, 513)
                if len(data) != st.st_size:
                    raise UnsafeState("changing release state")
                return data
            finally:
                os.close(item)
        finally:
            os.close(fd)

    def _write(self, name, data):
        fd = self._dirfd()
        path = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory, prefix=".release-", delete=False) as f:
                path = Path(f.name)
                os.fchmod(f.fileno(), 0o600)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            # State is checked under the common lock; never follow an existing link.
            self._read(name)
            os.replace(path, self.directory / name)
            os.fsync(fd)
            path = None
        finally:
            if path is not None:
                path.unlink(missing_ok=True)
            os.close(fd)


    @contextlib.contextmanager
    def lock(self):
        if self._locked:
            raise BusyRelease("release lock is not reentrant")
        fd = self._dirfd()
        try:
            try:
                lockfd = os.open("release.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise UnsafeState("symlinked release lock") from None
                raise
            try:
                st = os.fstat(lockfd)
                if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.geteuid() or st.st_mode & 0o077:
                    raise UnsafeState("unsafe release lock")
                try:
                    fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise BusyRelease("release busy") from exc
                os.fsync(fd)
                self._locked = True
                try:
                    yield self
                finally:
                    self._locked = False
                    fcntl.flock(lockfd, fcntl.LOCK_UN)
            finally:
                os.close(lockfd)
        finally:
            os.close(fd)

    def _selection(self):
        selected = self._read("events.enabled")
        if selected not in (None, b"enabled\n"):
            raise UnsafeState("invalid event selection")
        return selected is not None

    def begin(self, action, target, old_id, opt_in):
        if not self._locked:
            raise UnsafeState("release lock required")
        if action not in ("deploy", "rollback") or not HEX40.fullmatch(target) or not HEX64.fullmatch(old_id) or type(opt_in) is not bool:
            raise UnsafeState("invalid transition")
        selected = self._selection()
        pending = self._read("pending.json")
        if pending is not None:
            raise PendingTransition("pending release requires operator reconciliation")
        if action == "rollback" and selected and not opt_in:
            raise UnsafeState("cannot roll back active overlay to legacy release")
        # Marker and release bookkeeping are not one atomic transaction. Pending
        # is durable before any future adapter may revoke an old binding.
        data = {"action": action, "target": target, "old_id": old_id, "overlay": opt_in}
        self._write("pending.json", json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")

    def finish(self, new_id, old_id):
        if not self._locked or not HEX64.fullmatch(new_id) or not HEX64.fullmatch(old_id) or new_id == old_id:
            raise IdentityMismatch("invalid replacement identity")
        pending = self._read("pending.json")
        if pending is None:
            raise PendingTransition("no pending transition")
        try:
            data = json.loads(pending)
        except (ValueError, UnicodeError) as exc:
            raise UnsafeState("invalid pending transition") from None
        if data.get("old_id") != old_id or not HEX64.fullmatch(data.get("old_id", "")) or type(data.get("overlay")) is not bool:
            raise IdentityMismatch("old identity mismatch")
        # There is no installed host collector proof. Never promote an arbitrary
        # well-formed ID, clear the sticky pending gate or select the overlay.
        raise UnsafeState("host integration for exact-ID handoff is absent")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "probe":
        sys.exit("offline lock probe only; host integration absent")
    try:
        with ReleaseGate(sys.argv[2]).lock():
            pass
    except BusyRelease as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
