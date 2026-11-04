"""SENJU-MEM-001: expected-failing journal identity regression tests.

These tests specify the desired v2 invariant; the current v1 writer does not
implement genesis binding. Do not describe these tests as passing.
"""
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from memory.writer import IntegrityError, Journal, canonical


class JournalIdentityContractTests(unittest.TestCase):
    def test_empty_initialized_journal_rejects_manifest_identity_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = Journal(root)
            # The v1 implementation initializes on first append, not recover.
            journal._ensure_initialized()  # contract fixture only; no business event
            self.assertEqual(Journal(root).recover(), [])
            manifest = root / "manifest.json"
            marker = json.loads(manifest.read_bytes())
            marker["journal_id"] = str(uuid.uuid4())
            manifest.write_bytes(canonical(marker) + b"\n")
            with self.assertRaises(IntegrityError):
                Journal(root).recover()

    def test_nonempty_journal_rejects_manifest_identity_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Journal(root).append("key-1", "open", {"task": "A"})
            manifest = root / "manifest.json"
            marker = json.loads(manifest.read_bytes())
            marker["journal_id"] = str(uuid.uuid4())
            manifest.write_bytes(canonical(marker) + b"\n")
            with self.assertRaises(IntegrityError):
                Journal(root).recover()


if __name__ == "__main__":
    unittest.main()
