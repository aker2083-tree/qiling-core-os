"""Regression tests for command hash integrity during recovery."""
import json
import tempfile
import unittest
from pathlib import Path

from memory.writer import Journal, IntegrityError, canonical, digest


class CommandHashIntegrityTests(unittest.TestCase):
    def test_valid_event_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            Journal(directory).append("k", "open", {"task": "A"})
            self.assertEqual(len(Journal(directory).recover()), 1)

    def test_rehashed_outer_event_with_stale_command_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            Journal(directory).append("k", "open", {"task": "A"})
            path = Path(directory) / "events.jsonl"
            lines = path.read_bytes().splitlines(keepends=True)
            event = json.loads(lines[-1])
            event["command"]["payload"] = {"task": "B"}
            event.pop("event_hash")
            event["event_hash"] = digest(event)
            path.write_bytes(b"".join(lines[:-1]) + canonical(event) + b"\n")
            with self.assertRaises(IntegrityError):
                Journal(directory).recover()

    def test_non_mapping_command_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            Journal(directory).append("k", "open", {"task": "A"})
            path = Path(directory) / "events.jsonl"
            lines = path.read_bytes().splitlines(keepends=True)
            event = json.loads(lines[-1])
            event["command"] = ["not", "a", "mapping"]
            event["command_hash"] = digest(event["command"])
            event.pop("event_hash")
            event["event_hash"] = digest(event)
            path.write_bytes(b"".join(lines[:-1]) + canonical(event) + b"\n")
            with self.assertRaises(IntegrityError):
                Journal(directory).recover()


if __name__ == "__main__":
    unittest.main()
