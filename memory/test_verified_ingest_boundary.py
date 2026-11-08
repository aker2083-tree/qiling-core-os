"""SENJU-MEM-002 verified ingest boundary contract tests.

Fail-closed read-only wrapper over Journal.recover() + validate_handoff.
integrity_checked is metadata only; never elevates to verified identity or authority.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from memory.writer import Journal, IntegrityError
from memory.handoff_validator import validate_handoff


def verified_ingest(root, expected_journal_id):
    """Minimal fail-closed wrapper. Returns dict with events, projection, integrity_checked.

    Rejects absent or mismatched journal_id. On any integrity failure, zero accepted records.
    """
    root = Path(root)
    if not root.exists() or not (root / "manifest.json").exists():
        raise IntegrityError("absent or uninitialized storage; refusing empty recovery as success")
    j = Journal(root)
    events = j.recover()
    # Check journal_id against expected anchor
    if not (root / "manifest.json").exists():
        raise IntegrityError("manifest missing after recover")
    marker = json.loads((root / "manifest.json").read_bytes())
    actual_id = marker.get("journal_id")
    if actual_id != expected_journal_id:
        raise IntegrityError(f"journal_id mismatch: expected {expected_journal_id}, got {actual_id}")
    projection = validate_handoff(events)
    return {
        "events": events,
        "projection": projection,
        "integrity_checked": True,
        "authorization_granted": False,  # always
    }


class VerifiedIngestBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "j"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _seed_aba(self, j):
        j.append("handoff:A:proposal", "proposal",
                 {"event_id": "A1", "task_id": "SENJU-MEM-002", "reply_to": None},
                 actor_claim="wuxianqin", source_ref="test")
        j.append("handoff:B:review", "review",
                 {"event_id": "B1", "task_id": "SENJU-MEM-002", "reply_to": "A1", "correction": "ok"},
                 actor_claim="yingrufeng", source_ref="test")
        j.append("handoff:A:decision", "decision_proposed",
                 {"event_id": "A2", "task_id": "SENJU-MEM-002", "reply_to": "B1"},
                 actor_claim="wuxianqin", source_ref="test")
        return j

    def test_a_valid_aba_yields_projection_with_integrity_metadata(self):
        j = Journal(self.root)
        self._seed_aba(j)
        marker = json.loads((self.root / "manifest.json").read_bytes())
        expected_id = marker["journal_id"]
        result = verified_ingest(self.root, expected_id)
        self.assertTrue(result["integrity_checked"])
        self.assertFalse(result["authorization_granted"])
        proj = result["projection"]
        self.assertGreaterEqual(len(proj["accepted"]), 3)
        for rec in proj["accepted"]:
            self.assertFalse(rec["verified"])
            self.assertIsNone(rec["authority"])

    def test_b_one_byte_tamper_zero_accepted(self):
        j = Journal(self.root)
        self._seed_aba(j)
        marker = json.loads((self.root / "manifest.json").read_bytes())
        expected_id = marker["journal_id"]
        # Tamper one byte in events.jsonl
        log = self.root / "events.jsonl"
        data = log.read_bytes()
        if data:
            data = data[:10] + bytes([data[10] ^ 1]) + data[11:]
            log.write_bytes(data)
        with self.assertRaises(IntegrityError):
            verified_ingest(self.root, expected_id)

    def test_c_absent_root_rejects(self):
        absent = self.root / "nonexistent"
        with self.assertRaises(IntegrityError):
            verified_ingest(absent, "any-id")

    def test_d_different_journal_id_rejects(self):
        j = Journal(self.root)
        self._seed_aba(j)
        with self.assertRaises(IntegrityError):
            verified_ingest(self.root, "wrong-journal-id-xxxxxxxx")

    def test_e_accepted_remain_unverified(self):
        # Covered in test_a; explicit
        j = Journal(self.root)
        self._seed_aba(j)
        marker = json.loads((self.root / "manifest.json").read_bytes())
        result = verified_ingest(self.root, marker["journal_id"])
        for rec in result["projection"]["accepted"]:
            self.assertIs(rec["verified"], False)
            self.assertIsNone(rec["authority"])


if __name__ == "__main__":
    unittest.main()
