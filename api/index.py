import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone

class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/api", "/api/health"):
            self.respond(200, {"service":"senju-v0.1","status":"ready","mode":"preview-readonly","memory":"not-connected","timestamp":datetime.now(timezone.utc).isoformat()})
        else:
            self.respond(404, {"error":"not_found"})

    def do_POST(self):
        self.respond(501, {"error":"task_execution_not_enabled","message":"V0.1 preview only; no authenticated task executor or durable storage configured."})
