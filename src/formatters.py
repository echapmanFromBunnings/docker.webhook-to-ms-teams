"""Format GitHub webhook events into Teams-friendly payloads.

The Teams Power Automate workflow template "Post to a channel when a webhook
request is received" feeds the incoming request body into a "Post card in a
chat or channel" action, which requires a full Adaptive Card. The payload must
therefore be a `type: message` envelope with an Adaptive Card attachment whose
content has `"type": "AdaptiveCard"`.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

ADAPTIVE_CARD_VERSION = "1.4"
ADAPTIVE_CARD_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"


def _repo_link(repo: Dict[str, Any]) -> str:
    name = repo.get("full_name", repo.get("name", "unknown"))
    url = repo.get("html_url", "")
    return f"[{name}]({url})" if url else name


def _actor_link(actor: Dict[str, Any]) -> str:
    login = actor.get("login", "unknown")
    url = actor.get("html_url", "")
    return f"[{login}]({url})" if url else login


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_adaptive_card(title: str, markdown: str) -> Dict[str, Any]:
    """Wrap a title and markdown body in a Teams Adaptive Card message envelope."""
    body = [
        {
            "type": "TextBlock",
            "text": title,
            "weight": "Bolder",
            "size": "Medium",
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": markdown,
            "wrap": True,
        },
    ]
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": ADAPTIVE_CARD_SCHEMA,
                    "type": "AdaptiveCard",
                    "version": ADAPTIVE_CARD_VERSION,
                    "body": body,
                    "msteams": {"width": "Full"},
                },
            }
        ],
    }


def format_push(event: Dict[str, Any]) -> Tuple[str, str]:
    repo = event.get("repository", {})
    pusher = event.get("pusher", {})
    commits = event.get("commits", [])
    ref = event.get("ref", "unknown")
    branch = ref.split("/")[-1] if "/" in ref else ref

    title = f"Push to {repo.get('full_name', repo.get('name', 'repository'))}"
    lines = [
        f"Push to {_repo_link(repo)} on `{branch}` by {_actor_link(pusher)}",
        f"**When:** {_ts()}",
    ]
    if commits:
        lines.append("**Commits:**")
        for commit in commits[:7]:
            msg = commit.get("message", "").splitlines()[0]
            sha = commit.get("id", "")[:7]
            url = commit.get("url", "")
            lines.append(f"- `{sha}` [{msg}]({url})" if url else f"- `{sha}` {msg}")
        if len(commits) > 7:
            lines.append(f"- ... and {len(commits) - 7} more")

    return title, "\n\n".join(lines)


def format_pull_request(event: Dict[str, Any]) -> Tuple[str, str]:
    pr = event.get("pull_request", {})
    repo = event.get("repository", {})
    action = event.get("action", "updated")
    user = pr.get("user", {})
    prtitle = pr.get("title", "Untitled")
    url = pr.get("html_url", "")
    state = pr.get("state", "")

    title = f"Pull Request {action.capitalize()}"
    lines = [
        f"**Pull Request {action.capitalize()}** in {_repo_link(repo)}",
        f"**[{prtitle}]({url})**",
        f"**Author:** {_actor_link(user)} | **State:** {state}",
        f"**When:** {_ts()}",
    ]
    body = pr.get("body")
    if body:
        lines.append(f"**Description:**\n\n{body[:500]}")

    return title, "\n\n".join(lines)


def format_issues(event: Dict[str, Any]) -> Tuple[str, str]:
    issue = event.get("issue", {})
    repo = event.get("repository", {})
    action = event.get("action", "updated")
    user = issue.get("user", {})
    issuetitle = issue.get("title", "Untitled")
    url = issue.get("html_url", "")
    state = issue.get("state", "")

    title = f"Issue {action.capitalize()}"
    lines = [
        f"**Issue {action.capitalize()}** in {_repo_link(repo)}",
        f"**[{issuetitle}]({url})**",
        f"**Author:** {_actor_link(user)} | **State:** {state}",
        f"**When:** {_ts()}",
    ]
    body = issue.get("body")
    if body:
        lines.append(f"**Description:**\n\n{body[:500]}")

    return title, "\n\n".join(lines)


def format_workflow_run(event: Dict[str, Any]) -> Tuple[str, str]:
    run = event.get("workflow_run", {})
    repo = event.get("repository", {})
    name = run.get("name", "Workflow")
    conclusion = run.get("conclusion", "")
    status = run.get("status", "")
    url = run.get("html_url", "")
    head_branch = run.get("head_branch", "")

    emoji = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "⏳"

    title = f"Workflow Run: {name}"
    lines = [
        f"**Workflow Run** in {_repo_link(repo)}",
        f"{emoji} **[{name}]({url})** `{head_branch}` — {status} {conclusion}".strip(),
        f"**When:** {_ts()}",
    ]

    return title, "\n\n".join(lines)


def format_release(event: Dict[str, Any]) -> Tuple[str, str]:
    release = event.get("release", {})
    repo = event.get("repository", {})
    action = event.get("action", "")
    tag = release.get("tag_name", "")
    name = release.get("name", tag)
    url = release.get("html_url", "")
    author = release.get("author", {})

    title = f"Release {action.capitalize()}"
    lines = [
        f"**Release {action.capitalize()}** in {_repo_link(repo)}",
        f"**[{name}]({url})** `{tag}`",
        f"**Author:** {_actor_link(author)}",
        f"**When:** {_ts()}",
    ]
    body = release.get("body")
    if body:
        lines.append(f"**Notes:**\n\n{body[:500]}")

    return title, "\n\n".join(lines)


def format_fallback(event_name: str, event: Dict[str, Any]) -> Tuple[str, str]:
    repo = event.get("repository", {})
    sender = event.get("sender", {})
    title = f"GitHub event: {event_name}"
    lines = [
        f"**GitHub event:** `{event_name}` in {_repo_link(repo)}",
        f"**Triggered by:** {_actor_link(sender)}",
        f"**When:** {_ts()}",
        f"```\n{json.dumps(event, indent=2)[:1200]}\n```",
    ]
    return title, "\n\n".join(lines)


def format_event(event_name: str, event: Dict[str, Any], fmt: str = "adaptive") -> Dict[str, Any]:
    """Return a Teams-ready payload dict.

    fmt="adaptive" (default) returns a full Adaptive Card message envelope,
    which is what the Teams workflow "Post card in a chat or channel" action
    requires. fmt="text" returns a simple {"text": ...} body for workflows that
    post plain text.
    """
    formatter = {
        "push": format_push,
        "pull_request": format_pull_request,
        "issues": format_issues,
        "workflow_run": format_workflow_run,
        "release": format_release,
    }.get(event_name)

    if formatter is None:
        title, markdown = format_fallback(event_name, event)
    else:
        title, markdown = formatter(event)

    if fmt == "text":
        return {"text": f"**{title}**\n\n{markdown}"}
    return build_adaptive_card(title, markdown)
