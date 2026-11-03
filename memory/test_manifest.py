"""SENJU-MEM-001 fail-closed journal regression tests."""
import tempfile
import unittest
from pathlib import Path
from memory.writer import Journal, IntegrityError


class MissingJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.journal = Journal(self.root)

    def test_missing_log_rejected(self):
        self.journal.append("k1", "open", {"task": "A"})
        (self.root / "events.jsonl").unlink()
        with self.assertRaises(IntegrityError):
            Journal(self.root).append("k2", "open", {})
        self.assertFalse((self.root / "events.jsonl").exists())

    def test_missing_manifest_rejected(self):
        self.journal.append("k1", "open", {})
        (self.root / "manifest.json").unlink()
        with self.assertRaises(IntegrityError):
            Journal(self.root).append("k2", "open", {})

    def test_empty_new_directory_initializes(self):
        result = self.journal.append("k1", "open", {})
        self.assertEqual(result["status"], "committed")
        self.assertEqual(len(Journal(self.root).recover()), 1)
        self.assertTrue((self.root / "manifest.json").exists())

    def test_corrupt_manifest_rejected(self):
        self.journal.append("k1", "open", {})
        (self.root / "manifest.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            Journal(self.root).recover()


if __name__ == "__main__":
    unittest.main()
