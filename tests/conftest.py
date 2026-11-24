# PLAN TASK: 9 | STUDENT TASK PACK: Day 15 | EVIDENCE: TD-08
# WHERE: shared test isolation for API and performance checks
# DO: point every app instance at a temporary database before the lifespan starts.
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def isolated_app(tmp_path):
    application = create_app()
    application.state.db_path = tmp_path / "test.db"
    application.state.allow_admin = True
    return application


@pytest.fixture()
def api_client(isolated_app):
    with TestClient(isolated_app, raise_server_exceptions=False) as test_client:
        assert test_client.post("/v1/admin/reset").status_code == 204
        yield test_client
