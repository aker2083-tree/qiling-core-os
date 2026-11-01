"""Fuzang V0.1: local SQLite prototype. Not a cloud or semantic-memory service."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

KINDS = {"identity", "event", "semantic", "reflection"}
AGENTS = {"wuxianqin", "yingrufeng", "senju", "owner"}

def utc_now():
    return datetime.now(timezone.utc).isoformat()

class FuzangStore:
    def __init__(self, path):
        self.path = str(Path(path))
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("""CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, agent TEXT NOT NULL,
            content TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1, superseded_by TEXT,
            FOREIGN KEY(superseded_by) REFERENCES memories(id)
        )""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS memory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, memory_id TEXT NOT NULL,
            action TEXT NOT NULL, actor TEXT NOT NULL, timestamp TEXT NOT NULL,
            details TEXT NOT NULL, FOREIGN KEY(memory_id) REFERENCES memories(id)
        )""")
        self.db.commit()

    def add(self, kind, agent, content, source, actor="owner"):
        if kind not in KINDS or agent not in AGENTS or actor not in AGENTS:
            raise ValueError("invalid kind or agent")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be nonempty")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source required")
        mid, now = str(uuid4()), utc_now()
        with self.db:
            self.db.execute("INSERT INTO memories(id,kind,agent,content,source,created_at) VALUES(?,?,?,?,?,?)",
                            (mid,kind,agent,content,source,now))
            self.db.execute("INSERT INTO memory_events(memory_id,action,actor,timestamp,details) VALUES(?,?,?,?,?)",
                            (mid,"created",actor,now,"{}"))
        return mid

    def get(self, mid):
        row = self.db.execute("SELECT id,kind,agent,content,source,created_at,revision,superseded_by FROM memories WHERE id=?", (mid,)).fetchone()
        return dict(zip(("id","kind","agent","content","source","created_at","revision","superseded_by"),row)) if row else None

    def search(self, text="", kind=None, limit=20, include_superseded=False):
        if kind is not None and kind not in KINDS:
            raise ValueError("invalid kind")
        if not isinstance(limit,int) or not 1 <= limit <= 100:
            raise ValueError("limit must be 1..100")
        sql = "SELECT id FROM memories WHERE instr(content, ?) > 0"
        args = [text]
        if kind:
            sql += " AND kind=?"; args.append(kind)
        if not include_superseded:
            sql += " AND superseded_by IS NULL"
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"; args.append(limit)
        return [self.get(r[0]) for r in self.db.execute(sql,args)]

    def revise(self, mid, new_content, source, actor="owner"):
        old = self.get(mid)
        if not old or old["superseded_by"]:
            raise ValueError("memory missing or already superseded")
        if actor not in AGENTS or not new_content.strip() or not source.strip():
            raise ValueError("invalid revision")
        new_id, now = str(uuid4()), utc_now()
        with self.db:
            self.db.execute("INSERT INTO memories(id,kind,agent,content,source,created_at,revision) VALUES(?,?,?,?,?,?,?)",
                            (new_id,old["kind"],old["agent"],new_content,source,now,old["revision"]+1))
            updated = self.db.execute("UPDATE memories SET superseded_by=? WHERE id=? AND superseded_by IS NULL", (new_id,mid))
            if updated.rowcount != 1:
                raise ValueError("concurrent revision")
            self.db.execute("INSERT INTO memory_events(memory_id,action,actor,timestamp,details) VALUES(?,?,?,?,?)",
                            (mid,"superseded",actor,now,json.dumps({"new_id":new_id})))
            self.db.execute("INSERT INTO memory_events(memory_id,action,actor,timestamp,details) VALUES(?,?,?,?,?)",
                            (new_id,"revised",actor,now,json.dumps({"previous_id":mid})))
        return new_id

    def history(self, mid):
        return [dict(zip(("action","actor","timestamp","details"),r)) for r in
                self.db.execute("SELECT action,actor,timestamp,details FROM memory_events WHERE memory_id=? ORDER BY id",(mid,))]

    def close(self):
        self.db.close()
