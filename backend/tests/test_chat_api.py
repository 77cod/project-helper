from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_session_can_answer_with_code_references(tmp_path: Path):
    sample_repo = tmp_path / "chat-repo"
    sample_repo.mkdir()
    (sample_repo / "README.md").write_text("# Chat Repo\n", encoding="utf-8")
    (sample_repo / "service.py").write_text(
        "def load_users():\n    return ['alice', 'bob']\n",
        encoding="utf-8",
    )

    app = create_app(
        {
            "database_url": f"sqlite+aiosqlite:///{tmp_path / 'chat.db'}",
            "workspace_root": str(tmp_path / "workspace"),
            "testing_repo_map": {
                "https://github.com/demo/chat-repo": str(sample_repo),
            },
            "analysis_delay_ms": 0,
        }
    )

    with TestClient(app) as client:
        analyze = client.post(
            "/api/projects/analyze",
            json={"repo_url": "https://github.com/demo/chat-repo"},
        ).json()

        chat = client.post(
            "/api/chat/sessions",
            json={"project_id": analyze["project_id"], "title": "源码提问"},
        )
        message = client.post(
            f"/api/chat/sessions/{chat.json()['id']}/messages",
            json={"question": "users 在哪里加载"},
        )

        assert chat.status_code == 200
        assert message.status_code == 200
        assert "service.py" in message.json()["answer"]
        assert message.json()["references"][0]["path"] == "service.py"


def test_chat_stream_endpoint_yields_chunks(tmp_path: Path):
    sample_repo = tmp_path / "stream-repo"
    sample_repo.mkdir()
    (sample_repo / "README.md").write_text("# Stream Repo\n", encoding="utf-8")
    (sample_repo / "service.py").write_text(
        "def load_users():\n    return ['alice', 'bob']\n",
        encoding="utf-8",
    )

    app = create_app(
        {
            "database_url": f"sqlite+aiosqlite:///{tmp_path / 'stream.db'}",
            "workspace_root": str(tmp_path / "workspace"),
            "testing_repo_map": {
                "https://github.com/demo/stream-repo": str(sample_repo),
            },
            "analysis_delay_ms": 0,
        }
    )

    with TestClient(app) as client:
        analyze = client.post(
            "/api/projects/analyze",
            json={"repo_url": "https://github.com/demo/stream-repo"},
        ).json()
        chat = client.post(
            "/api/chat/sessions",
            json={"project_id": analyze["project_id"], "title": "流式问答"},
        ).json()

        with client.stream(
            "POST",
            f"/api/chat/sessions/{chat['id']}/messages/stream",
            json={"question": "users 在哪里加载"},
        ) as response:
            body = "".join(response.iter_text())

        assert response.status_code == 200
        assert '"type": "chunk"' in body
        assert "service.py" in body
