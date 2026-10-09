from pathlib import Path


def test_image_healthcheck_runs_the_closed_readiness_probe():
    dockerfile = (Path(__file__).resolve().parents[2] / "Dockerfile").read_text()
    assert 'HEALTHCHECK --interval=30s --timeout=8s --start-period=30s --retries=3' in dockerfile
    assert 'CMD ["python", "manage.py", "publish_ready_event"]' in dockerfile


def test_image_uses_dedicated_unprivileged_identity_and_writable_static_root():
    dockerfile = (Path(__file__).resolve().parents[2] / "Dockerfile").read_text()
    assert "RUN mkdir -p /app/staticfiles && chown -R 10001:10001 /app/staticfiles" in dockerfile
    assert "USER 10001:10001" in dockerfile