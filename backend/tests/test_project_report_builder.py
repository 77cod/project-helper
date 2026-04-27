from pathlib import Path

from app.analyzers.project_report_builder import build_project_report


def test_build_project_report_extracts_basic_sections(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo App\n\nA tiny sample project.", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text("class DemoService:\n    pass\n", encoding="utf-8")

    report = build_project_report(tmp_path, "https://github.com/demo/demo-app")

    assert report["project"]["repo_url"] == "https://github.com/demo/demo-app"
    assert report["overview"]["title"] == "Demo App"
    assert "Python" in report["tech_stack"]["languages"]
    assert "FastAPI" in report["tech_stack"]["frameworks"]
    assert any(item["path"] == "src" for item in report["directory_structure"]["items"])
    assert report["core_modules"]
    assert report["data_flow"]["steps"]
    assert "模块职责拆分" in report["design_patterns"]["patterns"][0]
    assert report["reading_guide"]["difficulty"] == "beginner"
