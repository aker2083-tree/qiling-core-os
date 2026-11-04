"""SENJU-MEM-001 deterministic initialization-crash regression (POSIX)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from memory.writer import IntegrityError, Journal


class InitializationCrashTests(unittest.TestCase):
    def test_crash_after_manifest_directory_fsync_fails_closed(self):
        """A crash between durable manifest and log must not silently reset."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = Journal(root)
            original = journal._fsync_directory
            calls = 0

            def crash_after_first_directory_sync():
                nonlocal calls
                original()
                calls += 1
                if calls == 1:
                    raise RuntimeError("simulated process termination after manifest fsync")

            with patch.object(journal, "_fsync_directory",
                              side_effect=crash_after_first_directory_sync):
                with self.assertRaisesRegex(RuntimeError, "simulated process"):
                    journal.append("first", "open", {"task": "A"})

            self.assertTrue((root / "manifest.json").exists())
            self.assertFalse((root / "events.jsonl").exists())
            with self.assertRaises(IntegrityError):
                Journal(root).append("second", "open", {"task": "B"})
            self.assertFalse((root / "events.jsonl").exists())

    def test_crash_after_log_directory_fsync_allows_clean_recovery(self):
        """After both files are durable, an interruption before first append is recoverable."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = Journal(root)
            original = journal._fsync_directory
            calls = 0

            def crash_after_second_directory_sync():
                nonlocal calls
                original()
                calls += 1
                if calls == 2:
                    raise RuntimeError("simulated process termination after log fsync")

            with patch.object(journal, "_fsync_directory",
                              side_effect=crash_after_second_directory_sync):
                with self.assertRaisesRegex(RuntimeError, "simulated process"):
                    journal.append("first", "open", {"task": "A"})

            self.assertEqual(Journal(root).recover(), [])
            result = Journal(root).append("retry", "open", {"task": "A"})
            self.assertEqual(result["status"], "committed")
            self.assertEqual(len(Journal(root).recover()), 1)


if __name__ == "__main__":
    unittest.main()
