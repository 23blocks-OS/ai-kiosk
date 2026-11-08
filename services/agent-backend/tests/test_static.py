"""The public origin must serve the kiosk UI and nothing else from disk."""
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app  # noqa: E402

client = TestClient(app)


def test_ui_is_served():
    assert client.get("/apps/kiosk-intercambio/").status_code == 200
    assert client.get("/apps/kiosk-intercambio/app.js").status_code == 200
    assert client.get("/packages/shared-ui/agent.css").status_code == 200


def test_health_still_works():
    assert client.get("/health").status_code == 200


def test_repo_internals_are_not_served():
    for path in (
        "/.git/config",
        "/.git/HEAD",
        "/.env",
        "/.gitignore",
        "/services/agent-backend/main.py",
        "/services/agent-backend/.env.example",
        "/hardware/jetson/cloudflared/config.yml.example",
        "/packages/shared-ui/../../.git/config",
        "/apps/../.git/config",
        "/apps/%2e%2e/.git/config",
    ):
        assert client.get(path).status_code == 404, path
