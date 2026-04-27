from app.services.repo_url import normalize_github_url, project_slug


def test_normalize_github_url_removes_dot_git_and_www():
    normalized = normalize_github_url("https://www.github.com/openai/openai-python.git")

    assert normalized == "https://github.com/openai/openai-python"


def test_normalize_github_url_rejects_non_github_urls():
    try:
        normalize_github_url("https://gitlab.com/example/project")
    except ValueError as exc:
        assert "GitHub" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-GitHub URL")


def test_project_slug_uses_owner_and_repo_name():
    assert project_slug("https://github.com/tiangolo/fastapi") == "tiangolo__fastapi"
