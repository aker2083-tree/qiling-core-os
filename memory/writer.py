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
        with self.log.open("xb") as stream:
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
        with self.log.open("rb") as stream:
            for line in stream:
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
            event = dict(seq=len(events) + 1, prev_hash=previous,
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
