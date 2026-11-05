"""GENESIS-002 RED contract: journal identity must be bound to the event chain.

Intentionally fails against schema v1. Isolated feature branch only.
Run: python -m unittest memory.test_genesis_002_red -v
"""
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from memory.writer import Journal, IntegrityError, canonical


class Genesis002Red(unittest.TestCase):
    def test_manifest_journal_id_swap_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(directory)
            journal.append("once", "note", {"text": "original"})
            manifest_path = Path(directory) / "manifest.json"
            original = json.loads(manifest_path.read_bytes())
            replacement = dict(original, journal_id=str(uuid.uuid4()))
            self.assertNotEqual(original["journal_id"], replacement["journal_id"])
            manifest_path.write_bytes(canonical(replacement) + b"\n")
            # Replacing the manifest with a valid but unrelated identity must
            # not silently reinterpret existing committed events.
            with self.assertRaises(IntegrityError):
                Journal(directory).recover()


if __name__ == "__main__":
    unittest.main()
