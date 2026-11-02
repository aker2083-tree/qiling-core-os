"""Read-only BRIDGE-001 issue inbox parser.

This module parses *untrusted* GitHub issue comments. It never invokes tools,
authenticates a model, claims a task, or posts a reply.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import re

ID_PATTERN = re.compile(r"^BRIDGE-001-\d{8}-\d{6}-\d{2,}$")
HEADER_PATTERN = re.compile(r"^([a-z_]+):[ \t]*(.*)$")
STATUSES = {"proposed", "acknowledged", "in_progress", "done", "blocked"}
SENDERS = {"yingrufeng/grok", "wuxianqin/openai"}
REQUIRED = {"protocol", "message_id", "sender", "timestamp", "status"}


@dataclass(frozen=True)
class Envelope:
    comment_id: int
    author: str
    created_at: str | None
    message_id: str
    sender: str
    reply_to: str | None
    timestamp: str
    status: str
    body: str


def _time(value):
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if t.tzinfo is None:
            return None
        return t.astimezone(timezone.utc)
    except (ValueError, AttributeError):
        return None


def parse_comment(comment):
    """Return (envelope, errors). Never trust sender/timestamp as authentication."""
    raw = comment.get("body")
    if not isinstance(raw, str):
        return None, ["missing_body"]
    headers, text, in_body = {}, [], False
    for line in raw.splitlines():
        if not in_body:
            if not line.strip():
                if headers:
                    in_body = True
                continue
            m = HEADER_PATTERN.fullmatch(line)
            if m:
                key, value = m.groups()
                if key in headers:
                    return None, ["duplicate_header:" + key]
                headers[key] = value.strip()
                continue
            in_body = True
        text.append(line)
    missing = REQUIRED - headers.keys()
    errors = ["missing_header:" + key for key in sorted(missing)]
    if errors:
        return None, errors
    if headers["protocol"] != "bridge-v0.1":
        errors.append("invalid_protocol")
    if not ID_PATTERN.fullmatch(headers["message_id"]):
        errors.append("invalid_message_id")
    if headers["sender"] not in SENDERS:
        errors.append("unknown_sender")
    if headers["status"] not in STATUSES:
        errors.append("invalid_status")
    claimed_time = _time(headers["timestamp"])
    if claimed_time is None:
        errors.append("invalid_timestamp")
    native_time = _time(comment.get("created_at"))
    if native_time and claimed_time and abs(native_time - claimed_time) > timedelta(minutes=10):
        errors.append("timestamp_mismatch")
    content = "\n".join(text).strip() or headers.get("body", "").strip()
    if not content:
        errors.append("missing_content")
    reply_to = headers.get("reply_to") or None
    if reply_to and reply_to != "BRIDGE-001" and not ID_PATTERN.fullmatch(reply_to):
        errors.append("invalid_reply_to")
    cid = comment.get("id")
    if not isinstance(cid, int):
        errors.append("missing_native_comment_id")
    if errors:
        return None, errors
    author = comment.get("user", {})
    if isinstance(author, dict):
        author = author.get("login", "")
    return Envelope(cid, str(author or ""), comment.get("created_at"),
                    headers["message_id"], headers["sender"], reply_to,
                    headers["timestamp"], headers["status"], content), []


def scan_unanswered(comments, allowed_author=None):
    """Return (unanswered_proposals, rejected).

    Only strict, unique, unacknowledged proposals from the claimed Grok persona
    are candidates for *human or separately authenticated* review. This is NOT
    an authorization decision. Duplicate IDs are rejected on both occurrences.
    """
    valid, rejected = [], []
    for c in comments:
        envelope, errors = parse_comment(c)
        if errors:
            rejected.append({"comment_id": c.get("id"), "errors": errors})
        else:
            valid.append(envelope)
    counts = {}
    for m in valid:
        counts[m.message_id] = counts.get(m.message_id, 0) + 1
    unique = []
    for m in valid:
        if counts[m.message_id] > 1:
            rejected.append({"comment_id": m.comment_id, "errors": ["duplicate_message_id"]})
        elif allowed_author is not None and m.author != allowed_author:
            rejected.append({"comment_id": m.comment_id, "errors": ["unexpected_github_author"]})
        else:
            unique.append(m)
    ids = {m.message_id for m in unique}
    reply_ids = {m.reply_to for m in unique if m.reply_to}
    for m in unique:
        if m.reply_to not in (None, "BRIDGE-001") and m.reply_to not in ids:
            rejected.append({"comment_id": m.comment_id, "errors": ["missing_reply_parent"]})
    candidates = [m for m in unique
                  if m.sender == "yingrufeng/grok" and m.status == "proposed"
                  and m.message_id not in reply_ids
                  and (m.reply_to in (None, "BRIDGE-001") or m.reply_to in ids)]
    return candidates, rejected
