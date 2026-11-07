"""RED contract tests: accurate blockers and actual cross-process recovery."""
import json
import subprocess
import sys
import tempfile
import unittest

from memory.writer import Journal


class ProjectionRecoveryContract(unittest.TestCase):
    def test_blocker_cleared_on_reopen_and_close(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(root)
            j.append("open", "task_opened", {"task_id": "T", "goal": "recover"})
            j.append("block", "task_updated", {"task_id": "T", "status": "blocked", "reason": "awaiting evidence"})
            self.assertEqual(j.summarize_for_agents()["blocked"], [
                {"task_id": "T", "reason": "awaiting evidence"}
            ])
            j.append("unblock", "task_updated", {"task_id": "T", "status": "open"})
            self.assertEqual(j.summarize_for_agents()["blocked"], [])
            j.append("block2", "task_updated", {"task_id": "T", "status": "blocked", "reason": "new issue"})
            j.append("close", "task_closed", {"task_id": "T"})
            self.assertEqual(j.summarize_for_agents()["blocked"], [])
            self.assertEqual(j.summarize_for_agents()["open_tasks"], [])

    def test_fresh_python_interpreter_recovers_same_projection(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(root)
            j.append("task", "task_opened", {"task_id": "T", "goal": "restart"})
            j.append("evidence", "observation", {"task_id": "T", "result_reference": "sha:example"})
            before = j.summarize_for_agents()
            code = "import json,sys; from memory.writer import Journal; print(json.dumps(Journal(sys.argv[1]).summarize_for_agents(), sort_keys=True))"
            result = subprocess.run(
                [sys.executable, "-c", code, root],
                capture_output=True, text=True, check=True,
            )
            after = json.loads(result.stdout)
            self.assertEqual(before, after)
            self.assertEqual(after["open_tasks"][0]["task_id"], "T")
            self.assertIn("sha:example", after["evidence_refs"])


if __name__ == "__main__":
    unittest.main()
