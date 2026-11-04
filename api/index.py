"""Senju's first read-only tool: inspect its own public GitHub repository."""
import json
import os
import hmac
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REPO = "aker2083-tree/qiling-core-os"
API = "https://api.github.com/repos/" + REPO

def github_get(path):
    # Paths are fixed by this module; never accept arbitrary URLs from callers.
    req = Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "senju-v0.1-readonly"})
    with urlopen(req, timeout=7) as response:
        return json.load(response)

def inspect_repository():
    repo = github_get("")
    prs = github_get("/pulls?state=open&per_page=20")
    commits = github_get("/commits?per_page=5")
    return {
        "task_id": "SENJU-001",
        "source": "github-public-api",
        "repository": REPO,
        "default_branch": repo.get("default_branch"),
        "open_pull_requests": [{"number": p["number"], "title": p["title"], "url": p["html_url"]} for p in prs],
        "recent_commits": [{"sha": c["sha"][:12], "message": c["commit"]["message"].splitlines()[0]} for c in commits],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "observation": "live_read_only",
        "evaluation": "manual_review_required",
        "reflection": "not_implemented",
        "memory_write": "not_implemented",
    }

def run_allowlisted_task(task_id):
    if task_id != "SENJU-001":
        raise ValueError("task_not_allowlisted")
    observation = inspect_repository()
    evaluation = {
        "success": True,
        "evidence": "github_public_api_response",
        "requires_human_review": True,
    }
    return {
        "agent": "senju",
        "task_id": task_id,
        "state": "completed",
        "plan": ["read_public_repository", "read_open_pull_requests", "read_recent_commits", "evaluate_observation"],
        "observation": observation,
        "evaluation": evaluation,
        "reflection": "Read-only execution verified; no autonomous memory write or external side effect.",
        "memory_write": "not_connected",
    }

class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in ("/api", "/api/index.py", "/api/health"):
            return self.respond(200, {"service":"senju-v0.1", "status":"ready", "capability":"github_readonly", "memory":"not_connected"})
        if path == "/api/project-status":
            if not self.authorized():
                return self.respond(401, {"error":"unauthorized"})
            try:
                return self.respond(200, inspect_repository())
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
                return self.respond(502, {"error":"github_unavailable", "type":type(exc).__name__})
        return self.respond(404, {"error":"not_found"})

    def authorized(self):
        secret = os.environ.get("SENJU_READ_TOKEN")
        if not secret:
            return False  # fail closed until configured in Vercel
        supplied = self.headers.get("Authorization", "")
        return hmac.compare_digest(supplied, "Bearer " + secret)

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path != "/api/tasks/run":
            return self.respond(404, {"error":"not_found"})
        if not self.authorized():
            return self.respond(401, {"error":"unauthorized"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond(400, {"error":"invalid_length"})
        if size <= 0 or size > 2048:
            return self.respond(413, {"error":"invalid_body_size"})
        try:
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or set(payload) != {"task_id"}:
                return self.respond(400, {"error":"invalid_task"})
            if payload["task_id"] != "SENJU-001":
                return self.respond(403, {"error":"task_not_allowlisted"})
            return self.respond(200, run_allowlisted_task(payload["task_id"]))
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, {"error":"invalid_json"})
        except (HTTPError, URLError, TimeoutError, KeyError) as exc:
            return self.respond(502, {"error":"github_unavailable", "type":type(exc).__name__})
