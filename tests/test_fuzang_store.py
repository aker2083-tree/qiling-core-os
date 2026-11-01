import os
import tempfile
import unittest
from fuzang_store import FuzangStore

class FuzangTests(unittest.TestCase):
    def test_restart_search_and_revision(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "memory.sqlite3")
            s = FuzangStore(path)
            old = s.add("event","wuxianqin","BRIDGE-001 complete","github:issue/2")
            s.close()
            s = FuzangStore(path)
            self.assertEqual(s.get(old)["source"],"github:issue/2")
            new = s.revise(old,"BRIDGE-001 reviewed","github:issue/2#comment",actor="yingrufeng")
            self.assertEqual(s.get(old)["superseded_by"],new)
            self.assertEqual(len(s.search("BRIDGE-001")),1)
            self.assertEqual(s.search("BRIDGE-001")[0]["id"],new)
            self.assertEqual(s.get(new)["revision"],2)
            self.assertEqual(s.history(old)[-1]["action"],"superseded")
            s.close()

    def test_validation(self):
        with tempfile.TemporaryDirectory() as d:
            s = FuzangStore(os.path.join(d,"test.sqlite3"))
            with self.assertRaises(ValueError):
                s.add("unknown","wuxianqin","hello","source")
            with self.assertRaises(ValueError):
                s.add("event","wuxianqin","hello","")
            s.close()

if __name__ == "__main__":
    unittest.main()
