from __future__ import annotations

import io
import shutil
import subprocess
import zipfile
from pathlib import Path

import httpx

from app.core.config import Settings
from app.services.repo_url import project_slug


class RepoManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def prepare_repo(self, repo_url: str) -> Path:
        workspace_root = self.settings.workspace_root
        workspace_root.mkdir(parents=True, exist_ok=True)
        target = workspace_root / project_slug(repo_url)

        testing_source = self.settings.testing_repo_map.get(repo_url)
        if testing_source:
            source_path = Path(testing_source)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source_path, target)
            return target

        if target.exists():
            return target

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            return target
        except subprocess.CalledProcessError:
            return self._download_archive_fallback(repo_url, target)

    def _download_archive_fallback(self, repo_url: str, target: Path) -> Path:
        owner, repo = repo_url.rstrip("/").rsplit("/", 2)[-2:]
        errors: list[str] = []

        for branch in ("main", "master"):
            archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
            try:
                response = httpx.get(archive_url, follow_redirects=True, timeout=60.0)
                response.raise_for_status()
                self._extract_archive(response.content, target)
                return target
            except Exception as exc:  # pragma: no cover
                errors.append(f"{branch}: {exc}")

        joined = " | ".join(errors) if errors else "unknown error"
        raise RuntimeError(
            "无法通过 git clone 访问 GitHub，且源码压缩包下载也失败了。"
            f" 已尝试分支 main/master。详细信息：{joined}"
        )

    def _extract_archive(self, archive_bytes: bytes, target: Path) -> None:
        if target.exists():
            shutil.rmtree(target)

        temp_root = target.parent / f"{target.name}__tmp"
        if temp_root.exists():
            shutil.rmtree(temp_root)
        temp_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            archive.extractall(temp_root)

        extracted_roots = [path for path in temp_root.iterdir() if path.is_dir()]
        if not extracted_roots:
            raise RuntimeError("下载到的源码压缩包为空。")

        shutil.move(str(extracted_roots[0]), str(target))
        shutil.rmtree(temp_root, ignore_errors=True)
