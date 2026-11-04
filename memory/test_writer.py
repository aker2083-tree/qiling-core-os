import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from memory.writer import Journal, IdempotencyConflict, IntegrityError


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.j = Journal(self.tmp.name)

    def test_idempotent_retry(self):
        a = self.j.append("k", "open", {"task": "A"})
        b = Journal(self.tmp.name).append("k", "open", {"task": "A"})
        self.assertEqual(b["status"], "already_committed")
        self.assertEqual(a["event"]["event_hash"], b["event"]["event_hash"])
        self.assertEqual(len(self.j.recover()), 1)

    def test_conflict(self):
        self.j.append("k", "open", {"task": "A"})
        with self.assertRaises(IdempotencyConflict):
            self.j.append("k", "open", {"task": "B"})

    def test_reject_truncated_tail(self):
        self.j.append("k", "open", {})
        with (Path(self.tmp.name) / "events.jsonl").open("ab") as stream:
            stream.write(b'{"partial":')
        with self.assertRaises(IntegrityError):
            self.j.append("k2", "open", {})

    def test_new_process_recovers(self):
        self.j.append("k", "open", {"task": "A"})
        code = ("from memory.writer import Journal; import sys; "
                "j=Journal(sys.argv[1]); "
                "assert len(j.recover())==1; "
                "assert j.append('k','open',{'task':'A'})['status']=='already_committed'")
        subprocess.run([sys.executable, "-c", code, self.tmp.name],
                       check=True, timeout=10)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            self.j.append("k", "open", {"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
