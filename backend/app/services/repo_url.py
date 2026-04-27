from urllib.parse import urlparse


def normalize_github_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    host = parsed.netloc.lower().removeprefix("www.")

    if host != "github.com":
        raise ValueError("Only public GitHub repositories are supported.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub repository URL must include owner and repo name.")

    owner, repo = parts[0], parts[1].removesuffix(".git")
    return f"https://github.com/{owner}/{repo}"


def project_slug(repo_url: str) -> str:
    normalized = normalize_github_url(repo_url)
    _, owner, repo = normalized.rsplit("/", 2)
    return f"{owner}__{repo}"
