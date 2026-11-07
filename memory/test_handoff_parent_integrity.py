"""Contract for handoff graph validation; journal is never rewritten."""
import tempfile
import unittest
from memory.writer import Journal
from memory.handoff_validator import validate_handoff

class HandoffParentIntegrity(unittest.TestCase):
    def test_invalid_links_are_quarantined_and_valid_chain_survives(self):
        with tempfile.TemporaryDirectory() as root:
            j = Journal(root)
            def put(eid, task="T", parent=None, kind="review"):
                j.append("key:"+eid, kind, {"event_id":eid,"task_id":task,"reply_to":parent},
                         actor_claim="unverified-agent",source_ref="test:fixture")
            put("A1",kind="proposal")
            put("missing",parent="NONE")
            put("forward",parent="later")
            put("cross",task="OTHER",parent="A1")
            put("B1",parent="A1")
            put("A2",parent="B1",kind="decision_proposed")
            put("later",kind="proposal")
            j.append("different-key","review",{"event_id":"B1","task_id":"T","reply_to":"A1"})
            put("child-of-invalid",parent="missing")
            before = j.log.read_bytes()
            result = validate_handoff(j.recover())
            self.assertEqual([x["event_id"] for x in result["accepted"]],["A1","B1","A2","later"])
            self.assertEqual({x["event_id"]:x["reason"] for x in result["quarantined"]},
              {"missing":"missing_or_forward_parent","forward":"missing_or_forward_parent",
               "cross":"cross_task_parent","B1":"duplicate_event_id",
               "child-of-invalid":"quarantined_parent"})
            self.assertFalse(result["authorization_granted"])
            self.assertTrue(all(x["authority"] is None and not x["verified"] for x in result["accepted"]))
            self.assertEqual(before,j.log.read_bytes())
if __name__ == "__main__":
    unittest.main()
