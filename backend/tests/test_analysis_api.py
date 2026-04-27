from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_analyze_endpoint_runs_and_returns_report(tmp_path: Path):
    sample_repo = tmp_path / "sample-repo"
    sample_repo.mkdir()
    (sample_repo / "README.md").write_text("# Sample Repo\n", encoding="utf-8")
    (sample_repo / "app.py").write_text("print('hi')\n", encoding="utf-8")

    app = create_app(
        {
            "database_url": f"sqlite+aiosqlite:///{tmp_path / 'app.db'}",
            "workspace_root": str(tmp_path / "workspace"),
            "testing_repo_map": {
                "https://github.com/demo/sample-repo": str(sample_repo),
            },
            "analysis_delay_ms": 0,
        }
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/projects/analyze",
            json={"repo_url": "https://github.com/demo/sample-repo"},
        )
        payload = response.json()

        assert response.status_code == 202
        assert payload["cached"] is False
        assert payload["status"] in {"queued", "running", "completed"}

        report_response = client.get(f"/api/projects/{payload['project_id']}/report")
        assert report_response.status_code == 200
        assert report_response.json()["overview"]["title"] == "Sample Repo"


def test_analyze_endpoint_uses_cache_for_existing_project(tmp_path: Path):
    sample_repo = tmp_path / "cached-repo"
    sample_repo.mkdir()
    (sample_repo / "README.md").write_text("# Cached Repo\n", encoding="utf-8")
    (sample_repo / "main.py").write_text("print('cache')\n", encoding="utf-8")

    app = create_app(
        {
            "database_url": f"sqlite+aiosqlite:///{tmp_path / 'app.db'}",
            "workspace_root": str(tmp_path / "workspace"),
            "testing_repo_map": {
                "https://github.com/demo/cached-repo": str(sample_repo),
            },
            "analysis_delay_ms": 0,
        }
    )
    with TestClient(app) as client:
        first = client.post(
            "/api/projects/analyze",
            json={"repo_url": "https://github.com/demo/cached-repo"},
        )
        second = client.post(
            "/api/projects/analyze",
            json={"repo_url": "https://github.com/demo/cached-repo"},
        )

        assert first.status_code == 202
        assert second.status_code == 200
        assert second.json()["cached"] is True
