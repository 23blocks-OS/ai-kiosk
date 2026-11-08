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


def test_root_goes_to_selector_and_keeps_query():
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/apps/launcher/"
    r = client.get("/?mode=remote", follow_redirects=False)
    assert r.headers["location"] == "/apps/launcher/?mode=remote"


def test_selector_page_and_its_target_exist():
    page = client.get("/apps/launcher/")
    assert page.status_code == 200
    assert 'href="../kiosk-intercambio/"' in page.text
    assert client.get("/apps/launcher/app.js").status_code == 200
    assert client.get("/apps/launcher/styles.css").status_code == 200
    assert client.get("/apps/kiosk-intercambio/").status_code == 200
