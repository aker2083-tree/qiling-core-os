import unittest
from bridge_inbox import parse_comment, scan_unanswered


def msg(cid, message_id, sender="yingrufeng/grok", status="proposed",
        reply_to="BRIDGE-001", author="aker2083-tree", timestamp="2026-11-03T02:00:00Z",
        created_at="2026-11-03T02:00:05Z"):
    return {
        "id": cid, "user": {"login": author}, "created_at": created_at,
        "body": ("protocol: bridge-v0.1\n"
                 f"message_id: {message_id}\n"
                 f"sender: {sender}\n"
                 f"reply_to: {reply_to}\n"
                 f"timestamp: {timestamp}\n"
                 f"status: {status}\n\n"
                 "Review the public read-only task contract.")
    }


A = "BRIDGE-001-20261103-020000-31"
B = "BRIDGE-001-20261103-020100-32"


class BridgeInboxTests(unittest.TestCase):
    def test_unanswered_proposal_and_ack(self):
        proposal = msg(101, A)
        self.assertEqual([m.message_id for m in scan_unanswered([proposal], "aker2083-tree")[0]], [A])
        ack = msg(102, B, sender="wuxianqin/openai", status="acknowledged",
                  reply_to=A, timestamp="2026-11-03T02:01:00Z",
                  created_at="2026-11-03T02:01:05Z")
        self.assertEqual(scan_unanswered([proposal, ack], "aker2083-tree")[0], [])

    def test_duplicate_ids_rejected(self):
        candidates, rejected = scan_unanswered([msg(101, A), msg(102, A)])
        self.assertEqual(candidates, [])
        self.assertEqual(sum("duplicate_message_id" in r["errors"] for r in rejected), 2)

    def test_native_author_mismatch(self):
        candidates, rejected = scan_unanswered([msg(101, A, author="other")], "aker2083-tree")
        self.assertEqual(candidates, [])
        self.assertIn("unexpected_github_author", rejected[0]["errors"])

    def test_timestamp_mismatch_and_missing_protocol(self):
        envelope, errors = parse_comment(msg(101, A, timestamp="2026-11-04T02:00:00Z"))
        self.assertIsNone(envelope)
        self.assertIn("timestamp_mismatch", errors)
        invalid = msg(101, A)
        invalid["body"] = invalid["body"].replace("protocol: bridge-v0.1\n", "")
        self.assertIn("missing_header:protocol", parse_comment(invalid)[1])

    def test_ack_is_not_actionable(self):
        self.assertEqual(scan_unanswered([msg(101, A, status="acknowledged")])[0], [])

    def test_untrusted_sender_label_is_not_authorization(self):
        env, errors = parse_comment(msg(101, A))
        self.assertEqual(errors, [])
        self.assertEqual(env.sender, "yingrufeng/grok")
        self.assertEqual(env.author, "aker2083-tree")

    def test_duplicate_header_and_missing_parent(self):
        invalid = msg(101, A)
        invalid["body"] = "status: proposed\n" + invalid["body"]
        self.assertIn("duplicate_header:status", parse_comment(invalid)[1])
        candidates, rejected = scan_unanswered([msg(102, B, reply_to=A)])
        self.assertEqual(candidates, [])
        self.assertIn("missing_reply_parent", rejected[0]["errors"])


if __name__ == "__main__":
    unittest.main()
