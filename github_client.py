import logging
import re
import subprocess
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """Base error for GitHub client operations."""


class PRParseError(GitHubClientError):
    """Could not parse the pull request URL."""


class ReviewerAssignmentError(GitHubClientError):
    """Failed to assign reviewers via GitHub API."""


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL.

    Args:
        url: GitHub pull request URL like https://github.com/owner/repo/pull/123

    Returns:
        Tuple of (owner, repo, pr_number)

    Raises:
        PRParseError: If the URL doesn't match the expected format.
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise PRParseError(
            f"Invalid PR URL: `{url}`\n"
            "Expected format: `https://github.com/owner/repo/pull/123`"
        )
    return match.group(1), match.group(2), int(match.group(3))


class GitHubClient:
    """Thin wrapper around the GitHub REST API for reviewer assignment."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10.0,
        )

    def assign_reviewers(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        reviewers: list[str],
        team_reviewers: list[str] | None = None,
    ) -> dict:
        """Request reviewers on a pull request.

        Uses the REST API for regular users and `gh` CLI for Copilot.

        Raises:
            ReviewerAssignmentError: On any API failure.
        """
        copilot_reviewers = [r for r in reviewers if r.lower() == "copilot"]
        regular_reviewers = [r for r in reviewers if r.lower() != "copilot"]

        # Assign Copilot via gh CLI
        for _ in copilot_reviewers:
            self._assign_copilot(owner, repo, pr_number)

        # Assign regular users via REST API
        result = {}
        if regular_reviewers or team_reviewers:
            result = self._assign_via_api(owner, repo, pr_number, regular_reviewers, team_reviewers)

        return result

    def _assign_copilot(self, owner: str, repo: str, pr_number: int) -> None:
        """Assign Copilot as reviewer using gh CLI."""
        cmd = [
            "gh", "pr", "edit", str(pr_number),
            "--repo", f"{owner}/{repo}",
            "--add-reviewer", "@copilot",
        ]
        logger.info("Assigning Copilot via gh CLI: %s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                raise ReviewerAssignmentError(
                    f"Failed to assign Copilot: {result.stderr.strip()}"
                )
        except FileNotFoundError:
            raise ReviewerAssignmentError(
                "GitHub CLI (`gh`) is not installed. "
                "Copilot can only be assigned as reviewer via `gh` CLI."
            )

    def _assign_via_api(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        reviewers: list[str],
        team_reviewers: list[str] | None = None,
    ) -> dict:
        """Assign regular users/teams via the GitHub REST API."""
        url = f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
        body: dict = {"reviewers": reviewers}
        if team_reviewers:
            body["team_reviewers"] = team_reviewers

        response = self._client.post(url, json=body)

        if response.status_code == 201:
            return response.json()

        if response.status_code == 422:
            detail = response.json().get("message", "Unprocessable Entity")
            raise ReviewerAssignmentError(
                f"GitHub rejected the request: {detail}\n"
                "Make sure all reviewers are collaborators of the repository."
            )
        elif response.status_code == 404:
            raise ReviewerAssignmentError(
                f"PR not found: `{owner}/{repo}#{pr_number}`\n"
                "Check that the repository exists and the token has access."
            )
        elif response.status_code == 403:
            raise ReviewerAssignmentError(
                "Permission denied. The GitHub token may lack `pull_requests: write` scope."
            )
        else:
            raise ReviewerAssignmentError(
                f"GitHub API error ({response.status_code}): {response.text}"
            )

    def get_pr_info(self, owner: str, repo: str, pr_number: int) -> dict | None:
        """Fetch basic PR info (title, state) for confirmation messages."""
        response = self._client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        if response.status_code == 200:
            return response.json()
        return None

    def close(self):
        self._client.close()
