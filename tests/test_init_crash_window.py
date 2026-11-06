"""SENJU-MEM-001: deterministic initialization crash-window regression tests.

Run: python -m unittest discover -s tests -p 'test_init_crash_window.py' -v
POSIX-only (journal uses fcntl and directory fsync).
"""
import json
import tempfile
import unittest
from pathlib import Path

from memory.writer import IntegrityError, Journal


class InitCrashWindowTests(unittest.TestCase):
    def test_manifest_fsynced_but_log_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(directory)
            original = journal._fsync_directory
            calls = 0

            def crash_after_manifest_directory_fsync():
                nonlocal calls
                original()
                calls += 1
                if calls == 1:
                    raise RuntimeError("simulated crash after manifest directory fsync")

            journal._fsync_directory = crash_after_manifest_directory_fsync
            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                journal.append("k1", "test", {"value": 1})

            manifest = Path(directory) / "manifest.json"
            log = Path(directory) / "events.jsonl"
            self.assertTrue(manifest.exists())
            self.assertFalse(log.exists())
            before = manifest.read_bytes()
            journal_id = json.loads(before)["journal_id"]
            self.assertTrue(journal_id)

            reopened = Journal(directory)
            with self.assertRaises(IntegrityError):
                reopened.recover()
            with self.assertRaises(IntegrityError):
                reopened.append("k2", "test", {"value": 2})
            self.assertEqual(manifest.read_bytes(), before)
            self.assertFalse(log.exists())

    def test_completed_empty_initialization_keeps_identity_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(directory)
            original = journal._fsync_directory
            calls = 0

            def stop_after_empty_log_directory_fsync():
                nonlocal calls
                original()
                calls += 1
                if calls == 2:
                    raise RuntimeError("simulated crash after empty log fsync")

            journal._fsync_directory = stop_after_empty_log_directory_fsync
            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                journal.append("k1", "test", {"value": 1})

            manifest = Path(directory) / "manifest.json"
            log = Path(directory) / "events.jsonl"
            before = manifest.read_bytes()
            self.assertTrue(log.exists())
            self.assertEqual(log.read_bytes(), b"")

            reopened = Journal(directory)
            self.assertEqual(reopened.recover(), [])
            self.assertEqual(reopened.append("k1", "test", {"value": 1})["status"], "committed")
            self.assertEqual(manifest.read_bytes(), before)
            self.assertEqual(len(Journal(directory).recover()), 1)


if __name__ == "__main__":
    unittest.main()
