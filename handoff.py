"""Offline, auditable task handoff. No external actions or AI API calls."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BOARD = Path(__file__).with_name("task_board.json")
AGENTS = {"wuxianqin", "yingrufeng"}
STATES = {"todo", "in_progress", "review", "done", "blocked"}

def handoff(task_id, from_agent, to_agent, note, board=BOARD):
    if from_agent not in AGENTS or to_agent not in AGENTS:
        raise ValueError("Unknown agent")
    if not note.strip():
        raise ValueError("Handoff note required")
    data = json.loads(Path(board).read_text(encoding="utf-8"))
    matches = [task for task in data["tasks"] if task["id"] == task_id]
    if len(matches) != 1:
        raise ValueError("Task ID must match exactly one task")
    task = matches[0]
    if task.get("assignee") != from_agent:
        raise ValueError("Only the recorded assignee can hand off")
    if task.get("status") not in STATES or task["status"] == "done":
        raise ValueError("Task cannot be handed off in this state")
    task.setdefault("history", []).append({
        "event": "handoff", "from": from_agent, "to": to_agent,
        "note": note, "at": datetime.now(timezone.utc).isoformat()
    })
    task["assignee"] = to_agent
    task["status"] = "review"
    board = Path(board)
    fd, temp = tempfile.mkstemp(dir=board.parent, prefix=".task_board_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.write("\n")
        os.replace(temp, board)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return task

if __name__ == "__main__":
    print("Import handoff(task_id, from_agent, to_agent, note) to use.")
