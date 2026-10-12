"""Activation contracts: Compose opt-in and release fail-closed preflight."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "compose.events.yml"


def _config(tmp_path, *files, host_dir=None):
    (tmp_path / ".env").write_text("SECRET_KEY=local-test-only\n")
    env = os.environ.copy()
    env.update(DB_NAME="test", DB_USER="test", DB_PASSWORD="test")
    if host_dir is not None:
        env["SAAS_EVENT_HOST_DIR"] = str(host_dir)
    else:
        env.pop("SAAS_EVENT_HOST_DIR", None)
    return subprocess.run(
        ["docker", "compose", "--project-directory", str(tmp_path),
         *[part for f in files for part in ("-f", str(f))], "config", "--format", "json"],
        text=True, capture_output=True, env=env,
    )


def test_event_overlay_is_opt_in_and_preserves_base_network_and_static(tmp_path):
    base = _config(tmp_path, ROOT / "compose.yml", ROOT / "compose.prod.yml")
    assert base.returncode == 0, base.stderr
    plain = json.loads(base.stdout)["services"]["web"]
    assert not plain.get("volumes")
    assert "SAAS_EVENT_SOURCE_DIR" not in plain.get("environment", {})
    enabled = _config(tmp_path, ROOT / "compose.yml", ROOT / "compose.prod.yml", OVERLAY,
                      host_dir=tmp_path / "source")
    assert enabled.returncode == 0, enabled.stderr
    web = json.loads(enabled.stdout)["services"]["web"]
    assert web["networks"] == plain["networks"]
    assert web["environment"]["SAAS_EVENT_SOURCE_DIR"] == "/run/saas-vendedor/events"
    assert len(web["volumes"]) == 1
    mount = web["volumes"][0]
    assert mount["type"] == "bind"
    assert mount["source"] == str(tmp_path / "source")
    assert mount["target"] == "/run/saas-vendedor/events"
    assert mount.get("read_only", False) is False
    # Some Compose versions omit the default false key in rendered config.
    assert mount.get("bind", {}).get("create_host_path", False) is False
    assert "create_host_path: false" in OVERLAY.read_text()
    assert web.get("user", plain.get("user")) == plain.get("user")
    assert json.loads(enabled.stdout)["services"]["db"]["volumes"] == json.loads(base.stdout)["services"]["db"]["volumes"]


def test_overlay_requires_explicit_host_directory(tmp_path):
    result = _config(tmp_path, ROOT / "compose.yml", ROOT / "compose.prod.yml", OVERLAY)
    assert result.returncode != 0
    assert "SAAS_EVENT_HOST_DIR" in result.stderr


def test_web_restart_policy_persists_across_host_reboot(tmp_path):
    result = _config(tmp_path, ROOT / "compose.yml", ROOT / "compose.prod.yml")
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["services"]["web"]["restart"] == "unless-stopped"
    assert config["services"]["db"]["restart"] == "unless-stopped"
