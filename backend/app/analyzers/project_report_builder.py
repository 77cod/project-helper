from __future__ import annotations

from pathlib import Path


LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".vue": "Vue",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
}


def build_project_report(project_path: Path, repo_url: str) -> dict:
    readme_title = _readme_title(project_path)
    languages = sorted(_detect_languages(project_path))
    frameworks = sorted(_detect_frameworks(project_path))
    tree_lines = _directory_tree_lines(project_path)
    core_modules = _core_modules(project_path)

    return {
        "project": {
            "repo_url": repo_url,
            "path": str(project_path),
        },
        "overview": {
            "title": readme_title or project_path.name,
            "summary": _build_summary(project_path, languages, frameworks),
        },
        "tech_stack": {
            "languages": languages,
            "frameworks": frameworks,
        },
        "directory_structure": {
            "items": _top_level_items(project_path),
            "tree": "\n".join(tree_lines),
        },
        "core_modules": core_modules,
        "data_flow": {
            "steps": _data_flow_steps(project_path, core_modules),
        },
        "design_patterns": {
            "patterns": _design_patterns(project_path),
        },
        "reading_guide": {
            "difficulty": "beginner",
            "steps": [
                "先看 README，理解这个项目想解决什么问题。",
                "再从目录结构入手，找到入口文件和核心模块。",
                "最后结合问答功能追踪具体代码细节。",
            ],
        },
    }


def _readme_title(project_path: Path) -> str | None:
    for name in ("README.md", "readme.md", "README.MD"):
        candidate = project_path / name
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("#"):
                    return line.lstrip("#").strip()
    return None


def _detect_languages(project_path: Path) -> set[str]:
    languages: set[str] = set()
    for path in project_path.rglob("*"):
        if path.is_file():
            language = LANGUAGE_EXTENSIONS.get(path.suffix.lower())
            if language:
                languages.add(language)
    return languages or {"Unknown"}


def _detect_frameworks(project_path: Path) -> set[str]:
    frameworks: set[str] = set()
    requirements = project_path / "requirements.txt"
    if requirements.exists():
        content = requirements.read_text(encoding="utf-8", errors="ignore").lower()
        if "fastapi" in content:
            frameworks.add("FastAPI")

    package_json = project_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        if '"vue"' in content:
            frameworks.add("Vue")

    return frameworks


def _top_level_items(project_path: Path) -> list[dict]:
    items: list[dict] = []
    for child in sorted(project_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if child.name.startswith("."):
            continue
        items.append(
            {
                "path": child.name,
                "kind": "directory" if child.is_dir() else "file",
            }
        )
    return items


def _build_summary(project_path: Path, languages: list[str], frameworks: list[str]) -> str:
    primary_language = languages[0] if languages else "Unknown"
    framework_text = "、".join(frameworks) if frameworks else "通用脚本/库"
    return (
        f"这是一个以 {primary_language} 为主的开源项目，当前检测到的主要技术方向是 {framework_text}。"
        f" 你可以先从 {project_path.name or '项目根目录'} 的 README 和入口文件开始理解整体思路。"
    )


def _directory_tree_lines(project_path: Path) -> list[str]:
    lines = [project_path.name]
    for child in sorted(project_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))[:12]:
        prefix = "└─ " if child.is_file() else "├─ "
        lines.append(f"{prefix}{child.name}")
    return lines


def _core_modules(project_path: Path) -> list[dict]:
    modules: list[dict] = []
    for path in sorted(project_path.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".js", ".ts", ".vue"}:
            continue
        relative = path.relative_to(project_path).as_posix()
        modules.append(
            {
                "path": relative,
                "role": _guess_module_role(relative),
            }
        )
        if len(modules) >= 5:
            break
    return modules or [{"path": "N/A", "role": "暂未识别到典型源码模块"}]


def _guess_module_role(relative_path: str) -> str:
    lowered = relative_path.lower()
    if "main" in lowered or "app" in lowered:
        return "很像程序入口，通常从这里启动整个项目。"
    if "service" in lowered:
        return "更像业务逻辑层，负责把具体功能组织起来。"
    if "api" in lowered or "route" in lowered:
        return "更像接口层，负责接收请求并把结果返回出去。"
    if "model" in lowered or "schema" in lowered:
        return "更像数据结构定义层，描述系统里有哪些数据。"
    return "这是一个值得优先阅读的核心源码文件。"


def _data_flow_steps(project_path: Path, core_modules: list[dict]) -> list[str]:
    first_module = core_modules[0]["path"] if core_modules else "入口文件"
    return [
        f"用户或外部系统先触发 {first_module} 一类的入口位置。",
        "入口层再把请求交给业务逻辑层处理。",
        "业务逻辑层会继续读取配置、文件或其他模块，整理成最终结果。",
        "最后系统把结果返回给调用方，或者写入本地文件与数据库。",
    ]


def _design_patterns(project_path: Path) -> list[str]:
    patterns = ["模块职责拆分：目录和文件已经在按功能分层，适合先理解每层负责什么。"]
    if (project_path / "src").exists():
        patterns.append("按源码目录集中管理：核心逻辑放进 src，有利于把业务代码和配置文件分开。")
    if (project_path / "requirements.txt").exists() or (project_path / "package.json").exists():
        patterns.append("依赖声明外置：通过依赖文件管理技术栈，方便快速判断项目生态。")
    return patterns
