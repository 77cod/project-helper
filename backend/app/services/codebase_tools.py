from __future__ import annotations

from pathlib import Path


class CodebaseTools:
    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path

    def list_files(self, limit: int = 30) -> list[str]:
        files: list[str] = []
        for path in sorted(self.project_path.rglob("*")):
            if path.is_file():
                files.append(path.relative_to(self.project_path).as_posix())
            if len(files) >= limit:
                break
        return files

    def read_file(self, relative_path: str, max_chars: int = 1200) -> str:
        target = self.project_path / relative_path
        return target.read_text(encoding="utf-8", errors="ignore")[:max_chars]

    def search_code(self, query: str, limit: int = 3) -> list[dict]:
        matches: list[dict] = []
        tokens = [token for token in query.lower().split() if token.strip()]
        for path in sorted(self.project_path.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".ts", ".vue", ".md", ".json"}:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            lowered = content.lower()
            if any(token in lowered for token in tokens):
                relative = path.relative_to(self.project_path).as_posix()
                matches.append(
                    {
                        "path": relative,
                        "snippet": content[:240].strip(),
                    }
                )
            if len(matches) >= limit:
                break
        return matches
