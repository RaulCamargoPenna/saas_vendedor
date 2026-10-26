from pathlib import Path


def test_deploy_requires_successful_master_test_workflow():
    deploy = (Path(__file__).resolve().parents[2] / ".github/workflows/deploy.yml").read_text()
    assert "workflow_run:" in deploy
    assert "completed" in deploy
    assert "success" in deploy
    assert "head_branch == 'master'" in deploy
    assert "head_repository.full_name" in deploy
    assert "&& false" in deploy
    assert "branches:\n      - master" not in deploy


def test_pull_request_ci_runs_suite_and_image_smoke():
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/test.yml").read_text()
    assert "pull_request:" in workflow
    assert "pytest -q" in workflow
    assert "docker build" in workflow
    assert "collectstatic --noinput" in workflow


def test_image_healthcheck_runs_the_closed_readiness_probe():
    dockerfile = (Path(__file__).resolve().parents[2] / "Dockerfile").read_text()
    assert 'HEALTHCHECK --interval=30s --timeout=8s --start-period=30s --retries=3' in dockerfile
    assert 'CMD ["python", "manage.py", "publish_ready_event"]' in dockerfile


def test_image_uses_dedicated_unprivileged_identity_and_writable_static_root():
    dockerfile = (Path(__file__).resolve().parents[2] / "Dockerfile").read_text()
    assert "RUN mkdir -p /app/staticfiles && chown -R 10001:10001 /app/staticfiles" in dockerfile
    assert "USER 10001:10001" in dockerfile