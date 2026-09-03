import pytest
from fastapi.testclient import TestClient

from engine import workspace
from server.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "WORKSPACES_DIR", tmp_path / "workspaces")
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as c:
        yield c
