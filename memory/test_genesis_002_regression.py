"""GENESIS-002 compatibility and tamper regression (isolated branch, POSIX)."""
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from memory.writer import Journal, IntegrityError, canonical, digest


class Genesis002Regression(unittest.TestCase):
    def test_v1_fixture_recover_and_append_without_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {"schema_version": 1, "journal_id": str(uuid.uuid4())}
            command = {"idempotency_key": "old", "kind": "note",
                       "payload": {"text": "legacy"}, "actor_claim": "", "source_ref": ""}
            event = {"seq": 1, "prev_hash": "0" * 64, "command": command,
                     "command_hash": digest(command)}
            event["event_hash"] = digest(event)
            (root / "manifest.json").write_bytes(canonical(manifest) + b"\n")
            (root / "events.jsonl").write_bytes(canonical(event) + b"\n")
            journal = Journal(root)
            self.assertEqual(journal.recover(), [event])
            self.assertEqual(journal.append("old", "note", {"text": "legacy"})["status"],
                             "already_committed")
            self.assertEqual(journal.append("new", "note", {"text": "after restart"})["status"],
                             "committed")
            self.assertEqual(json.loads((root / "manifest.json").read_bytes()), manifest)
            recovered = Journal(root).recover()
            self.assertEqual(len(recovered), 2)
            self.assertTrue(all("journal_id" not in item for item in recovered))

    def test_v2_event_payload_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(directory)
            journal.append("once", "note", {"text": "original"})
            log = Path(directory) / "events.jsonl"
            event = json.loads(log.read_bytes())
            event["command"]["payload"]["text"] = "tampered"
            log.write_bytes(canonical(event) + b"\n")
            with self.assertRaises(IntegrityError):
                Journal(directory).recover()

    def test_unknown_schema_rejected_without_rewriting(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(directory)
            journal.append("once", "note", {"text": "original"})
            manifest = Path(directory) / "manifest.json"
            marker = json.loads(manifest.read_bytes())
            marker["schema_version"] = 999
            modified = canonical(marker) + b"\n"
            manifest.write_bytes(modified)
            with self.assertRaises(IntegrityError):
                Journal(directory).recover()
            with self.assertRaises(IntegrityError):
                Journal(directory).append("new", "note", {})
            self.assertEqual(manifest.read_bytes(), modified)

    def test_v2_restart_preserves_identity_and_hash_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(directory)
            journal.append("first", "note", {"n": 1})
            manifest = json.loads((Path(directory) / "manifest.json").read_bytes())
            self.assertEqual(manifest["schema_version"], 2)
            reopened = Journal(directory)
            reopened.append("second", "note", {"n": 2})
            events = reopened.recover()
            self.assertEqual([e["seq"] for e in events], [1, 2])
            self.assertTrue(all(e["journal_id"] == manifest["journal_id"] for e in events))
            self.assertEqual(events[1]["prev_hash"], events[0]["event_hash"])


if __name__ == "__main__":
    unittest.main()
