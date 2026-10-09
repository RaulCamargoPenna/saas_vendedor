"""Optional, closed-code producer for the VPS Control ADR 0003 host collector.

Filesystem metadata alone does not authenticate a producer; host provisioning must
isolate this directory and pin its exact container ID in the collector config.
"""

import fcntl
import json
import os
import stat
import time
import uuid


class EventPublicationError(ValueError):
    """Fixed diagnostic without producer data or exception chaining."""


def publish_event(source_dir, code, *, now=None, capture_ns=None):
    """Replace the private, bounded event window with one fixed event."""
    # No tracked, durable post-success job hook exists in this checkout.
    if code != "app.ready":
        raise EventPublicationError("invalid event code")
    if now is None:
        now = int(time.time())
    if capture_ns is None:
        capture_ns = time.time_ns()
    if type(now) is not int or not 0 <= now <= 253402300799:
        raise EventPublicationError("invalid timestamp")
    if type(capture_ns) is not int or capture_ns < 0:
        raise EventPublicationError("invalid capture time")
    path = os.fspath(source_dir)
    if not isinstance(path, str) or not path.startswith("/") or any(
        part in ("", ".", "..") for part in path.split("/")[1:]
    ):
        raise EventPublicationError("invalid source directory")
    payload = (json.dumps({"version": 1, "timestamp": now, "code": code},
                          separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
    directory_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.split("/")[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                              dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        info = os.fstat(directory_fd)
        if (info.st_uid != os.getuid() or info.st_gid != os.getgid()
                or stat.S_IMODE(info.st_mode) != 0o700):
            raise EventPublicationError("invalid source directory")
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        name = "events.jsonl"
        try:
            previous = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            previous = None
        if previous is not None and (not stat.S_ISREG(previous.st_mode)
                or previous.st_uid != os.getuid() or previous.st_gid != os.getgid()
                or stat.S_IMODE(previous.st_mode) != 0o600 or previous.st_nlink != 1
                or previous.st_mtime_ns >= capture_ns):
            raise EventPublicationError("invalid previous publication")
        if previous is not None and previous.st_mtime >= now - 60:
            if not 0 < previous.st_size <= 8192:
                raise EventPublicationError("invalid previous publication")
            old_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                             dir_fd=directory_fd)
            try:
                old_info = os.fstat(old_fd)
                old_bytes = os.read(old_fd, 8193)
                if (old_info.st_ino, old_info.st_dev, old_info.st_mtime_ns) != (
                        previous.st_ino, previous.st_dev, previous.st_mtime_ns):
                    raise EventPublicationError("invalid previous publication")
            finally:
                os.close(old_fd)
            try:
                lines = old_bytes.splitlines(keepends=True)
                if not 1 <= len(lines) <= 40:
                    raise ValueError()
                for line in lines:
                    if len(line) > 256 or not line.endswith(b"\n"):
                        raise ValueError()
                    def unique_pairs(pairs):
                        record = {}
                        for key, value in pairs:
                            if key in record:
                                raise ValueError()
                            record[key] = value
                        return record

                    record = json.loads(line, object_pairs_hook=unique_pairs,
                                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                    if (type(record) is not dict or set(record) != {"version", "timestamp", "code"}
                            or type(record["version"]) is not int or record["version"] != 1
                            or type(record["timestamp"]) is not int
                            or record["code"] not in ("app.ready", "job.succeeded")
                            or not now - 60 <= record["timestamp"] <= now + 60
                            or record["timestamp"] > now):
                        raise ValueError()
            except (ValueError, UnicodeError, TypeError):
                # Do not chain JSONDecodeError: its .doc may retain private bytes.
                invalid = True
            else:
                invalid = False
            if invalid:
                raise EventPublicationError("invalid previous publication")
        temporary = ".events-" + uuid.uuid4().hex
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=directory_fd)
        try:
            try:
                os.write(fd, payload)
                os.utime(fd, ns=(capture_ns, capture_ns))
                if os.fstat(fd).st_mtime_ns != capture_ns:
                    raise EventPublicationError("unsupported publication timestamp")
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            os.fsync(directory_fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
    except OSError:
        raise EventPublicationError("event publication unavailable") from None
    finally:
        os.close(directory_fd)
