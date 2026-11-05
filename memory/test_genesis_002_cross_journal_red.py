"""GENESIS-002 G2 RED: reject transplanting an intact log to another journal.

Run on an authorized POSIX Python runner:
    python -m unittest memory.test_genesis_002_cross_journal_red -v

Expected RED against v1; no production writes or secrets.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from memory.writer import IntegrityError, Journal


class CrossJournalIdentityRed(unittest.TestCase):
    def test_foreign_event_log_must_not_recover_under_another_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            a, b = Path(root) / "a", Path(root) / "b"
            Journal(a).append("a-once", "note", {"origin": "a"})
            Journal(b).append("b-once", "note", {"origin": "b"})
            manifest_a = json.loads((a / "manifest.json").read_bytes())
            manifest_b = json.loads((b / "manifest.json").read_bytes())
            self.assertNotEqual(manifest_a["journal_id"], manifest_b["journal_id"])
            # Replace only B's events, keeping B's own valid manifest.
            shutil.copyfile(a / "events.jsonl", b / "events.jsonl")
            # A valid foreign hash chain is NOT a valid history of journal B.
            with self.assertRaises(IntegrityError):
                Journal(b).recover()


if __name__ == "__main__":
    unittest.main()
