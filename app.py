import logging
import os
import re

from flask import Flask, request as flask_request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from github_client import (
    GitHubClient,
    GitHubClientError,
    parse_pr_url,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Slack Bolt app -----------------------------------------------------------

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

github = GitHubClient(token=os.environ["GITHUB_TOKEN"])

# --- Helpers ------------------------------------------------------------------

USAGE = (
    "*Usage:*\n"
    "`/assign-reviewers <PR_URL> <reviewer1> [reviewer2] ...`\n\n"
    "*Example:*\n"
    "`/assign-reviewers https://github.com/acme/api/pull/42 octocat hubot`"
)


def _parse_command(text: str) -> tuple[str, list[str], list[str]]:
    """Parse the slash-command text into a PR URL and reviewer lists.

    Tokens prefixed with `team:` are treated as team reviewers.

    Returns:
        (pr_url, user_reviewers, team_reviewers)

    Raises:
        ValueError with a user-friendly message on bad input.
    """
    tokens = text.strip().split()

    if len(tokens) < 2:
        raise ValueError(f"Please provide a PR URL and at least one reviewer.\n\n{USAGE}")

    pr_url = tokens[0]
    if not re.search(r"github\.com/.+/.+/pull/\d+", pr_url):
        raise ValueError(f"`{pr_url}` doesn't look like a GitHub PR URL.\n\n{USAGE}")

    user_reviewers: list[str] = []
    team_reviewers: list[str] = []

    for token in tokens[1:]:
        # Strip leading @ if present (Slack sometimes adds it)
        name = token.lstrip("@")
        if name.startswith("team:"):
            team_reviewers.append(name.removeprefix("team:"))
        else:
            user_reviewers.append(name)

    if not user_reviewers and not team_reviewers:
        raise ValueError(f"No reviewers provided.\n\n{USAGE}")

    return pr_url, user_reviewers, team_reviewers


def _build_success_message(
    owner: str,
    repo: str,
    pr_number: int,
    reviewers: list[str],
    team_reviewers: list[str],
    pr_title: str | None,
) -> str:
    names = ", ".join(f"`{r}`" for r in reviewers)
    if team_reviewers:
        names += ", " + ", ".join(f"`team:{t}`" for t in team_reviewers)

    title_line = f"  *{pr_title}*\n" if pr_title else ""
    return (
        f":white_check_mark: Reviewers assigned to "
        f"<https://github.com/{owner}/{repo}/pull/{pr_number}|{owner}/{repo}#{pr_number}>\n"
        f"{title_line}"
        f"  Reviewers: {names}"
    )


# --- Slash command handler ----------------------------------------------------


@app.command("/assign-reviewers")
def handle_assign_reviewers(ack, command, respond):
    """Handle /assign-reviewers slash command."""
    ack()  # acknowledge within 3 seconds

    text: str = command.get("text", "").strip()

    if not text or text in ("help", "--help"):
        respond(USAGE)
        return

    # Parse input
    try:
        pr_url, reviewers, team_reviewers = _parse_command(text)
        owner, repo, pr_number = parse_pr_url(pr_url)
    except (ValueError, GitHubClientError) as exc:
        respond(f":x: {exc}")
        return

    # Assign reviewers via GitHub API
    try:
        github.assign_reviewers(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            reviewers=reviewers,
            team_reviewers=team_reviewers or None,
        )
    except GitHubClientError as exc:
        respond(f":x: {exc}")
        return

    # Fetch PR title for a nicer confirmation message
    pr_info = github.get_pr_info(owner, repo, pr_number)
    pr_title = pr_info["title"] if pr_info else None

    respond(_build_success_message(owner, repo, pr_number, reviewers, team_reviewers, pr_title))
    logger.info(
        "Assigned reviewers %s to %s/%s#%d (requested by %s)",
        reviewers + [f"team:{t}" for t in team_reviewers],
        owner,
        repo,
        pr_number,
        command.get("user_name", "unknown"),
    )


# --- Flask server -------------------------------------------------------------

flask_app = Flask(__name__)
flask_handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return flask_handler.handle(flask_request)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)
