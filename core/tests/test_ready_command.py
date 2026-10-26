import json
import http.client

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.mark.django_db
def test_ready_command_publishes_only_after_http_and_database_checks(tmp_path, monkeypatch):
    source = tmp_path / "events"
    source.mkdir(mode=0o700)
    monkeypatch.setenv("SAAS_EVENT_SOURCE_DIR", str(source))
    called = []

    class LocalConnection:
        def __init__(self, host, port, timeout):
            called.append((host, port, timeout))

        def request(self, method, path, headers):
            assert (method, path, headers) == (
                "GET", "/saas/", {"Host": "saas.raulcamargo.com.br"}
            )

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", LocalConnection)
    call_command("publish_ready_event")
    assert called == [("127.0.0.1", 8000, 3)]
    assert json.loads((source / "events.jsonl").read_text())["code"] == "app.ready"


@pytest.mark.django_db
def test_opt_out_still_checks_readiness_without_publication(tmp_path, monkeypatch):
    source = tmp_path / "events"
    source.mkdir(mode=0o700)
    monkeypatch.delenv("SAAS_EVENT_SOURCE_DIR", raising=False)
    monkeypatch.setattr(http.client, "HTTPConnection", lambda *args, **kwargs: type(
        "Local", (), {"request": lambda self, *a, **k: None,
                       "getresponse": lambda self: Response(), "close": lambda self: None})())
    call_command("publish_ready_event")
    assert not (source / "events.jsonl").exists()


@pytest.mark.django_db
def test_database_failure_does_not_publish_or_expose_error(tmp_path, monkeypatch):
    source = tmp_path / "events"
    source.mkdir(mode=0o700)
    monkeypatch.setenv("SAAS_EVENT_SOURCE_DIR", str(source))
    monkeypatch.setattr(http.client, "HTTPConnection", lambda *args, **kwargs: type(
        "Local", (), {"request": lambda self, *a, **k: None,
                       "getresponse": lambda self: Response(), "close": lambda self: None})())
    from core.management.commands import publish_ready_event

    class BrokenConnection:
        def cursor(self):
            raise RuntimeError("private-db-password-marker")

    monkeypatch.setattr(publish_ready_event, "connection", BrokenConnection())
    with pytest.raises(CommandError, match="^readiness unavailable$") as exc:
        call_command("publish_ready_event")
    assert "private-db-password-marker" not in str(exc.value)
    assert exc.value.__cause__ is None
    assert not (source / "events.jsonl").exists()


@pytest.mark.django_db
def test_readiness_never_follows_a_redirect_to_another_host(tmp_path, monkeypatch):
    source = tmp_path / "events"
    source.mkdir(mode=0o700)
    monkeypatch.setenv("SAAS_EVENT_SOURCE_DIR", str(source))
    # urlopen follows redirects; the fixed local connection must inspect 302 itself.
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())

    class RedirectConnection:
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ("127.0.0.1", 8000, 3)

        def request(self, method, path, headers):
            assert (method, path) == ("GET", "/saas/")

        def getresponse(self):
            return type("Redirect", (), {"status": 302})()

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", RedirectConnection)
    with pytest.raises(CommandError, match="readiness unavailable"):
        call_command("publish_ready_event")
    assert not (source / "events.jsonl").exists()