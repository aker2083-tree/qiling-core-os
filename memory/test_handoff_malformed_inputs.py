"""Malformed imported handoff records must not abort read-side recovery.

RED contract: current validator raises AttributeError for non-mapping events/commands.
No claim of upstream journal authenticity or actor authorization.
"""
import unittest
from memory.handoff_validator import validate_handoff


class HandoffMalformedInputContract(unittest.TestCase):
    def test_malformed_records_quarantined_without_losing_valid_chain(self):
        def ev(seq, eid, kind="review", parent=None):
            return {"seq": seq, "event_hash": "fixture-hash-" + str(seq),
                    "command": {"kind": kind, "actor_claim": "unverified",
                                "payload": {"event_id": eid, "task_id": "T",
                                            "reply_to": parent}}}

        events = [
            ev(1, "A1", "proposal"),
            "not-an-event",
            {"seq": 3, "event_hash": "bad-command", "command": "review"},
            {"seq": 4, "event_hash": "missing-command"},
            {"seq": 5, "event_hash": "bad-payload",
             "command": {"kind": "review", "payload": ["not-a-dict"]}},
            ev(6, "B1", parent="A1"),
            ev(7, "A2", "decision_proposed", parent="B1"),
        ]
        before = repr(events)
        result = validate_handoff(events)
        self.assertEqual([x["event_id"] for x in result["accepted"]],
                         ["A1", "B1", "A2"])
        self.assertEqual(len(result["quarantined"]), 4)
        self.assertEqual([x["source_index"] for x in result["quarantined"]],
                         [1, 2, 3, 4])
        self.assertTrue(all(isinstance(x["reason"], str) and x["reason"]
                            for x in result["quarantined"]))
        self.assertFalse(result["authorization_granted"])
        self.assertTrue(all(not x["verified"] and x["authority"] is None
                            for x in result["accepted"]))
        self.assertEqual(repr(events), before)


if __name__ == "__main__":
    unittest.main()
