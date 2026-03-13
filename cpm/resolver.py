import os

import requests
from requests import Session

from cpm.parser import Package

GITHUB_API = "https://api.github.com"


class ResolverError(Exception):
    pass


class RepoNotFoundError(ResolverError):
    pass


class NoTagsError(ResolverError):
    pass


class VersionNotFoundError(ResolverError):
    pass


def make_session() -> Session:
    token: str | None = os.environ.get("GITHUB_TOKEN")
    session = requests.Session()
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def _get_tags(
    owner: str, repo: str, session: Session, per_page: int = 100, page: int = 1
) -> list[str]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/tags"
    params = {"per_page": per_page, "page": page}

    try:
        resp = session.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        raise ResolverError(
            f"Network error when fetching tags for {owner}/{repo}: {e}"
        ) from e

    if resp.status_code == 404:
        raise RepoNotFoundError(f"Repository {owner}/{repo} not found or is private.")
    elif resp.status_code == 401:
        raise ResolverError("Bad GitHub token. Check your GITHUB_TOKEN.")
    elif resp.status_code == 403:
        msg = resp.json().get("message", "")
        if "rate limit" in msg.lower():
            raise ResolverError(
                "GitHub rate limit hit. Set GITHUB_TOKEN to get 5000 requests/hour."
            )
        raise ResolverError(f"GitHub access denied for {owner}/{repo}: {msg}")
    elif 500 <= resp.status_code < 600:
        raise ResolverError(
            f"GitHub API error ({resp.status_code}) for {owner}/{repo}."
        )

    try:
        data = resp.json()
    except ValueError as e:
        raise ResolverError(
            f"Invalid JSON response from GitHub for {owner}/{repo}"
        ) from e

    if not isinstance(data, list):
        raise ResolverError(f"Unexpected GitHub response structure for {owner}/{repo}")

    tags = [entry["name"] for entry in data if "name" in entry]
    return tags


def resolve(package: Package, session: Session) -> str:
    owner = package.owner
    repo = package.name

    tags = _get_tags(owner, repo, session)

    if not tags:
        raise NoTagsError(f"Repository {owner}/{repo} exists but has no tags.")

    if package.version == "latest":
        return tags[0]

    tag_str = str(package.version)
    if tag_str in tags:
        return tag_str

    page = 2
    while True:
        next_tags = _get_tags(owner, repo, session, page=page)
        if not next_tags:
            break
        if tag_str in next_tags:
            return tag_str
        page += 1

    raise VersionNotFoundError(
        f"Requested version {tag_str} not found in repository {owner}/{repo}. "
        f"Available tags (first page): {tags[:10]}{'...' if len(tags) > 10 else ''}"
    )
