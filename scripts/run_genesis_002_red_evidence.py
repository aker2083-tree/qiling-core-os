#!/usr/bin/env python3
"""GENESIS-002 exact-checkout RED evidence collector.

Run from the repository root on an authorized POSIX runner:
    python scripts/run_genesis_002_red_evidence.py

No secrets, network access, deployment, or writes to production state.
Creates a local JSON report; do not label RED as GREEN.
"""
import datetime
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "memory.test_genesis_002_red",
    "memory.test_genesis_002_cross_journal_red",
]


def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)


def main():
    rev = run("git", "rev-parse", "HEAD")
    if rev.returncode:
        print("ERROR: checkout commit SHA unavailable; refusing untraceable evidence", file=sys.stderr)
        return 2
    dirty = run("git", "status", "--porcelain")
    if dirty.returncode or dirty.stdout.strip():
        print("ERROR: working tree is not clean; refusing ambiguous evidence", file=sys.stderr)
        return 2
    results = []
    for test in TESTS:
        command = [sys.executable, "-m", "unittest", test, "-v"]
        completed = run(*command)
        results.append({
            "test": test,
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
    report = {
        "schema_version": 1,
        "task_id": "SENJU-MEM-001-GENESIS-002",
        "commit_sha": rev.stdout.strip(),
        "utc_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "tests": results,
        "interpretation": "RED evidence only; failing tests are expected before v2 implementation",
    }
    target = ROOT / "genesis_002_red_evidence.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {target.name} for commit {report['commit_sha']}")
    for item in results:
        print(f"{item['test']}: exit={item['exit_code']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
