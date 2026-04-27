from __future__ import annotations

import io
import subprocess
import zipfile
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.repo_manager import RepoManager


def test_prepare_repo_falls_back_to_archive_download_when_git_clone_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    settings = Settings(
        workspace_root=tmp_path / "workspace",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'app.db'}",
    )
    manager = RepoManager(settings)

    def fail_clone(*args, **kwargs):
        raise subprocess.CalledProcessError(
            128,
            ["git", "clone"],
            stderr="Failed to connect to github.com port 443",
        )

    downloaded = {"called": False}

    def fake_download(repo_url: str, target: Path) -> Path:
        downloaded["called"] = True
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text("# Downloaded\n", encoding="utf-8")
        return target

    monkeypatch.setattr(subprocess, "run", fail_clone)
    monkeypatch.setattr(manager, "_download_archive_fallback", fake_download)

    repo_path = manager.prepare_repo("https://github.com/demo/fallback-repo")

    assert downloaded["called"] is True
    assert (repo_path / "README.md").exists()


def test_extract_archive_moves_nested_root_into_target(tmp_path: Path):
    settings = Settings(
        workspace_root=tmp_path / "workspace",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'app.db'}",
    )
    manager = RepoManager(settings)
    target = tmp_path / "repo"

    archive_bytes = io.BytesIO()
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr("demo-main/README.md", "# Demo\n")
        archive.writestr("demo-main/src/app.py", "print('ok')\n")

    manager._extract_archive(archive_bytes.getvalue(), target)

    assert (target / "README.md").exists()
    assert (target / "src" / "app.py").exists()
