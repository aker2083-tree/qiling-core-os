"""SENJU-MEM-001 minimal durable command journal (POSIX, Python stdlib)."""
import fcntl
import hashlib
import json
import os
import uuid
from pathlib import Path


class IntegrityError(Exception):
    pass


class IdempotencyConflict(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Journal:
    def __init__(self, directory):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.log = self.root / "events.jsonl"
        self.lock = self.root / ".writer.lock"
        self.manifest = self.root / "manifest.json"

    def _fsync_directory(self):
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _ensure_initialized(self):
        # Must run under the exclusive writer lock.
        if self.manifest.exists() or self.log.exists():
            return
        marker = {"schema_version": 1, "journal_id": str(uuid.uuid4())}
        with self.manifest.open("xb") as stream:
            stream.write(canonical(marker) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        self._fsync_directory()
        # Genesis anchor binds journal identity into the log even with zero business events.
        genesis = {
            "type": "genesis",
            "schema_version": 1,
            "journal_id": marker["journal_id"],
        }
        with self.log.open("xb") as stream:
            stream.write(canonical(genesis) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        self._fsync_directory()

    def _load(self):
        events, keys, previous = [], {}, "0" * 64
        manifest_exists = self.manifest.exists()
        log_exists = self.log.exists()
        if manifest_exists != log_exists:
            raise IntegrityError("manifest/log missing: refusing implicit reset")
        if not manifest_exists:
            return events, keys, previous
        try:
            raw = self.manifest.read_bytes()
            marker = json.loads(raw)
            if (canonical(marker) + b"\n" != raw or
                    marker.get("schema_version") != 1 or
                    not isinstance(marker.get("journal_id"), str) or
                    not marker["journal_id"]):
                raise IntegrityError("invalid manifest")
        except (ValueError, TypeError, UnicodeError, AttributeError) as exc:
            raise IntegrityError("invalid manifest") from exc
        journal_id = marker["journal_id"]
        with self.log.open("rb") as stream:
            lines = stream.readlines()
        if not lines:
            raise IntegrityError("missing genesis anchor")
        # First line must be genesis bound to manifest journal_id
        first = lines[0]
        if not first.endswith(b"\n"):
            raise IntegrityError("partial event line")
        try:
            genesis = json.loads(first)
            if canonical(genesis) + b"\n" != first:
                raise IntegrityError("noncanonical event")
            if (genesis.get("type") != "genesis" or
                    genesis.get("schema_version") != 1 or
                    genesis.get("journal_id") != journal_id):
                raise IntegrityError("journal_id mismatch")
        except (ValueError, TypeError, UnicodeError, AttributeError) as exc:
            raise IntegrityError("invalid genesis") from exc
        for line in lines[1:]:
            if not line.endswith(b"\n"):
                raise IntegrityError("partial event line")
            try:
                event = json.loads(line)
                if canonical(event) + b"\n" != line:
                    raise IntegrityError("noncanonical event")
                h = event.pop("event_hash")
                if (event["seq"] != len(events) + 1 or
                        event["prev_hash"] != previous or digest(event) != h):
                    raise IntegrityError("broken event chain")
                if event.get("journal_id") != journal_id:
                    raise IntegrityError("journal_id mismatch")
                event["event_hash"] = h
                if (not isinstance(event.get("command"), dict) or
                        not isinstance(event.get("command_hash"), str) or
                        event["command_hash"] != digest(event["command"])):
                    raise IntegrityError("command hash mismatch")
                key = event["command"]["idempotency_key"]
                if key in keys:
                    raise IntegrityError("duplicate idempotency key")
                keys[key] = event
                events.append(event)
                previous = h
            except (ValueError, TypeError, KeyError, UnicodeError) as exc:
                raise IntegrityError("invalid event") from exc
        return events, keys, previous

    def append(self, idempotency_key, kind, payload, actor_claim="", source_ref=""):
        command = dict(idempotency_key=idempotency_key, kind=kind, payload=payload,
                       actor_claim=actor_claim, source_ref=source_ref)
        command_hash = digest(command)
        with self.lock.open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            self._ensure_initialized()
            events, keys, previous = self._load()
            if idempotency_key in keys:
                existing = keys[idempotency_key]
                if existing["command_hash"] != command_hash:
                    raise IdempotencyConflict(idempotency_key)
                return {"status": "already_committed", "event": existing}
            # Bind journal identity into every committed event (GENESIS-002)
            marker = json.loads(self.manifest.read_bytes())
            event = dict(seq=len(events) + 1, prev_hash=previous,
                         journal_id=marker["journal_id"],
                         command=command, command_hash=command_hash)
            event["event_hash"] = digest(event)
            with self.log.open("ab") as stream:
                stream.write(canonical(event) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            return {"status": "committed", "event": event}

    def recover(self):
        with self.lock.open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
            return self._load()[0]

    def summarize_for_agents(self):
        """Project shared state for dual-agent bootstrap (SENJU-CORE-DIRECTIVE-001).

        Returns a deterministic summary from the event log only.
        Platform memory is not consulted. actor_claim is recorded, not trusted.
        """
        events = self.recover()
        open_tasks = {}
        decisions = []
        blocked = []
        evidence_refs = []
        journal_id = None
        if self.manifest.exists():
            journal_id = json.loads(self.manifest.read_bytes()).get("journal_id")

        for event in events:
            cmd = event.get("command") or {}
            kind = cmd.get("kind")
            payload = cmd.get("payload") or {}
            ref = cmd.get("source_ref") or ""
            if kind == "task_opened":
                tid = payload.get("task_id") or cmd.get("idempotency_key")
                open_tasks[tid] = {
                    "task_id": tid,
                    "goal": payload.get("goal"),
                    "status": payload.get("status", "open"),
                    "risk_level": payload.get("risk_level", "low"),
                    "acceptance": payload.get("acceptance"),
                }
            elif kind == "task_updated":
                tid = payload.get("task_id")
                if tid in open_tasks:
                    if "status" in payload:
                        open_tasks[tid]["status"] = payload["status"]
                    if payload.get("status") == "blocked":
                        blocked.append({"task_id": tid, "reason": payload.get("reason")})
            elif kind == "task_closed":
                tid = payload.get("task_id")
                open_tasks.pop(tid, None)
                if payload.get("result_reference"):
                    evidence_refs.append(payload["result_reference"])
            elif kind == "decision_confirmed":
                decisions.append({
                    "decision_id": payload.get("decision_id") or cmd.get("idempotency_key"),
                    "summary": payload.get("summary"),
                    "source_ref": ref,
                })
            elif kind == "observation":
                if payload.get("result_reference"):
                    evidence_refs.append(payload["result_reference"])

        open_list = [t for t in open_tasks.values() if t.get("status") != "done"]
        return {
            "journal_id": journal_id,
            "open_tasks": open_list,
            "last_decisions": decisions[-5:],
            "blocked": blocked,
            "evidence_refs": evidence_refs[-10:],
            "event_count": len(events),
        }
