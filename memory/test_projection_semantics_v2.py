"""Projection semantics V0.2: identity, completed tasks, disagreement, proposed vs confirmed."""
import tempfile
import unittest

from memory.writer import Journal


class ProjectionSemanticsV2Tests(unittest.TestCase):
    def test_identity_completed_and_disagreement_projected(self):
        with tempfile.TemporaryDirectory() as directory:
            j = Journal(directory)
            j.append(
                "id-covenant",
                "identity_ref",
                {"doc": "docs/COVENANT.md", "title": "core covenant", "note": "master recognition"},
                actor_claim="yingrufeng/grok",
                source_ref="d1",
            )
            j.append(
                "task-a-open",
                "task_opened",
                {"task_id": "T-A", "goal": "do A", "status": "open", "priority": "P0"},
            )
            j.append(
                "task-b-open",
                "task_opened",
                {"task_id": "T-B", "goal": "do B", "status": "open"},
            )
            j.append(
                "task-b-close",
                "task_closed",
                {"task_id": "T-B", "result_reference": "commit:abc"},
            )
            j.append(
                "dec-prop",
                "decision_proposed",
                {"decision_id": "D1", "summary": "maybe use cloud snapshot"},
                actor_claim="wuxianqin/openai",
            )
            j.append(
                "dec-conf",
                "decision_confirmed",
                {"decision_id": "D0", "summary": "journal is source of truth"},
                actor_claim="wuxianqin/openai",
                source_ref="directive:CORE",
            )
            j.append(
                "dis-1",
                "disagreement",
                {
                    "disagreement_id": "DIS-1",
                    "topic": "upload full chat to github",
                    "positions": {"yingrufeng": "no full dump", "wuxianqin": "need more context"},
                    "reason": "noise vs auditability",
                    "evidence_refs": ["bridge:msg-1"],
                    "status": "open",
                },
            )
            s = j.summarize_for_agents()
            self.assertEqual(s["projection_schema_version"], 2)
            self.assertEqual(len(s["identity_refs"]), 1)
            self.assertEqual(s["identity_refs"][0]["doc"], "docs/COVENANT.md")
            open_ids = {t["task_id"] for t in s["open_tasks"]}
            self.assertEqual(open_ids, {"T-A"})
            self.assertEqual(s["completed_tasks"][-1]["task_id"], "T-B")
            self.assertIn("commit:abc", s["evidence_refs"])
            self.assertEqual(s["decisions_confirmed"][-1]["decision_id"], "D0")
            self.assertEqual(s["decisions_proposed"][-1]["decision_id"], "D1")
            self.assertEqual(s["last_decisions"][-1]["decision_id"], "D0")
            self.assertEqual(len(s["disagreements_open"]), 1)
            self.assertEqual(s["disagreements_open"][0]["disagreement_id"], "DIS-1")

    def test_disagreement_resolved_leaves_open_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            j = Journal(directory)
            j.append(
                "dis-1",
                "disagreement",
                {"disagreement_id": "DIS-1", "topic": "x", "status": "open"},
            )
            j.append(
                "dis-1-res",
                "disagreement_resolved",
                {"disagreement_id": "DIS-1", "resolution": "structured summary only"},
            )
            s = j.summarize_for_agents()
            self.assertEqual(s["disagreements_open"], [])

    def test_two_instances_same_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            j1 = Journal(directory)
            j1.append("id-1", "identity_ref", {"doc": "DOC", "title": "t"})
            j1.append("t1", "task_opened", {"task_id": "T1", "goal": "g", "status": "open"})
            s1 = j1.summarize_for_agents()
            s2 = Journal(directory).summarize_for_agents()
            self.assertEqual(s1["journal_id"], s2["journal_id"])
            self.assertEqual(s1["identity_refs"], s2["identity_refs"])
            self.assertEqual(s1["open_tasks"], s2["open_tasks"])
            self.assertEqual(s1["projection_schema_version"], s2["projection_schema_version"])


if __name__ == "__main__":
    unittest.main()
