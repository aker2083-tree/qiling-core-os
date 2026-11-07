"""SENJU-CORE: shared memory bootstrap summary must be recoverable across processes."""
import tempfile
import unittest

from memory.writer import Journal


class SummarizeForAgentsTests(unittest.TestCase):
    def test_two_processes_same_open_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            j1 = Journal(directory)
            j1.append(
                "task-mem-001",
                "task_opened",
                {
                    "task_id": "MEM-001",
                    "goal": "cross-session recover open tasks",
                    "status": "open",
                    "risk_level": "low",
                    "acceptance": "two processes same summary",
                },
                actor_claim="wuxianqin/openai",
                source_ref="directive:SENJU-CORE-DIRECTIVE-001",
            )
            j1.append(
                "obs-mem-001",
                "observation",
                {
                    "task_id": "MEM-001",
                    "result_reference": "commit:example",
                    "note": "structure doc added",
                },
            )
            summary1 = j1.summarize_for_agents()

            # New process (new Journal instance) recovers same shared state
            j2 = Journal(directory)
            summary2 = j2.summarize_for_agents()

            self.assertEqual(summary1["journal_id"], summary2["journal_id"])
            self.assertEqual(summary1["open_tasks"], summary2["open_tasks"])
            self.assertEqual(len(summary2["open_tasks"]), 1)
            self.assertEqual(summary2["open_tasks"][0]["task_id"], "MEM-001")
            self.assertIn("commit:example", summary2["evidence_refs"])
            self.assertEqual(summary1["event_count"], summary2["event_count"])

    def test_task_closed_removed_from_open(self):
        with tempfile.TemporaryDirectory() as directory:
            j = Journal(directory)
            j.append("t1", "task_opened", {"task_id": "T1", "goal": "g", "status": "open"})
            j.append("t1c", "task_closed", {"task_id": "T1", "result_reference": "done-ref"})
            s = j.summarize_for_agents()
            self.assertEqual(s["open_tasks"], [])
            self.assertIn("done-ref", s["evidence_refs"])


if __name__ == "__main__":
    unittest.main()
