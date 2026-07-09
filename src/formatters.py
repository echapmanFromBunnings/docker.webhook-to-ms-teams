"""Format GitHub webhook events into Teams-friendly payloads."""

import json
from datetime import datetime, timezone
from typing import Any, Dict


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


def format_push(event: Dict[str, Any]) -> Dict[str, Any]:
    repo = event.get("repository", {})
    pusher = event.get("pusher", {})
    commits = event.get("commits", [])
    ref = event.get("ref", "unknown")
    branch = ref.split("/")[-1] if "/" in ref else ref

    lines = [
        f"**Push** to {_repo_link(repo)} on `{branch}` by {_actor_link(pusher)}",
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

    return {"text": "\n\n".join(lines)}


def format_pull_request(event: Dict[str, Any]) -> Dict[str, Any]:
    pr = event.get("pull_request", {})
    repo = event.get("repository", {})
    action = event.get("action", "updated")
    user = pr.get("user", {})
    title = pr.get("title", "Untitled")
    url = pr.get("html_url", "")
    state = pr.get("state", "")

    lines = [
        f"**Pull Request {action.capitalize()}** in {_repo_link(repo)}",
        f"**[{title}]({url})**",
        f"**Author:** {_actor_link(user)} | **State:** {state}",
        f"**When:** {_ts()}",
    ]
    body = pr.get("body")
    if body:
        lines.append(f"**Description:**\n{body[:500]}")

    return {"text": "\n\n".join(lines)}


def format_issues(event: Dict[str, Any]) -> Dict[str, Any]:
    issue = event.get("issue", {})
    repo = event.get("repository", {})
    action = event.get("action", "updated")
    user = issue.get("user", {})
    title = issue.get("title", "Untitled")
    url = issue.get("html_url", "")
    state = issue.get("state", "")

    lines = [
        f"**Issue {action.capitalize()}** in {_repo_link(repo)}",
        f"**[{title}]({url})**",
        f"**Author:** {_actor_link(user)} | **State:** {state}",
        f"**When:** {_ts()}",
    ]
    body = issue.get("body")
    if body:
        lines.append(f"**Description:**\n{body[:500]}")

    return {"text": "\n\n".join(lines)}


def format_workflow_run(event: Dict[str, Any]) -> Dict[str, Any]:
    run = event.get("workflow_run", {})
    repo = event.get("repository", {})
    action = event.get("action", "")
    name = run.get("name", "Workflow")
    conclusion = run.get("conclusion", "")
    status = run.get("status", "")
    url = run.get("html_url", "")
    head_branch = run.get("head_branch", "")

    emoji = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "⏳"

    lines = [
        f"**Workflow Run** in {_repo_link(repo)}",
        f"{emoji} **[{name}]({url})** `{head_branch}` — {status} {conclusion}".strip(),
        f"**When:** {_ts()}",
    ]

    return {"text": "\n\n".join(lines)}


def format_release(event: Dict[str, Any]) -> Dict[str, Any]:
    release = event.get("release", {})
    repo = event.get("repository", {})
    action = event.get("action", "")
    tag = release.get("tag_name", "")
    name = release.get("name", tag)
    url = release.get("html_url", "")
    author = release.get("author", {})

    lines = [
        f"**Release {action.capitalize()}** in {_repo_link(repo)}",
        f"**[{name}]({url})** `{tag}`",
        f"**Author:** {_actor_link(author)}",
        f"**When:** {_ts()}",
    ]
    body = release.get("body")
    if body:
        lines.append(f"**Notes:**\n{body[:500]}")

    return {"text": "\n\n".join(lines)}


def format_fallback(event_name: str, event: Dict[str, Any]) -> Dict[str, Any]:
    repo = event.get("repository", {})
    sender = event.get("sender", {})
    lines = [
        f"**GitHub event:** `{event_name}` in {_repo_link(repo)}",
        f"**Triggered by:** {_actor_link(sender)}",
        f"**When:** {_ts()}",
        f"```json\n{json.dumps(event, indent=2)[:1500]}\n```",
    ]
    return {"text": "\n\n".join(lines)}


def format_event(event_name: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Return a Teams-ready payload dict with at least a `text` key."""
    formatter = {
        "push": format_push,
        "pull_request": format_pull_request,
        "issues": format_issues,
        "workflow_run": format_workflow_run,
        "release": format_release,
    }.get(event_name, lambda e: format_fallback(event_name, e))
    return formatter(event)
