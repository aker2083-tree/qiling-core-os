"""
千手秘 · 最小可驗證執行器 (Senju Minimal Runner)
目標：完成一次完整閉環，不執行高風險動作。
"""

import json
from datetime import datetime, timezone
from pathlib import Path

BOARD = Path(__file__).with_name("task_board.json")
LOG_DIR = Path(__file__).with_name("vault") / "observations"

def now():
    return datetime.now(timezone.utc).isoformat()

def load_board():
    return json.loads(BOARD.read_text(encoding="utf-8"))

def save_board(data):
    BOARD.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_observation(task_id, content):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)

def run_t001():
    """執行 T-001：讀取自身狀態 → 寫入觀察 → 更新任務狀態"""
    board = load_board()
    task = next((t for t in board["tasks"] if t["id"] == "T-001"), None)
    if not task:
        return {"error": "T-001 not found"}

    # 1. Plan
    plan = [
        "讀取 task_board 當前狀態",
        "讀取 agents.yaml 與核心思想文件存在性",
        "產生觀察紀錄",
        "更新任務狀態為 done 並寫入 history"
    ]

    # 2. Execute (low-risk, repo-internal only)
    observations = {
        "task_id": "T-001",
        "executed_at": now(),
        "plan": plan,
        "findings": {
            "task_board_exists": BOARD.exists(),
            "task_count": len(board.get("tasks", [])),
            "assignee": task.get("assignee"),
            "status_before": task.get("status"),
            "core_covenant_present": Path("docs/ZIZAI_GUANG_CORE_COVENANT_2026-10-28.md").exists(),
            "agents_yaml_present": Path("agents.yaml").exists(),
        },
        "result": "success",
        "notes": "第一次真實閉環完成。僅讀取本倉庫狀態，無外部副作用。"
    }

    # 3. Write observation to vault
    md = f"""# T-001 觀察紀錄

時間：{observations['executed_at']}
執行者：yingrufeng（影如風）

## 目標
{task.get('goal')}

## 規劃
""" + "\n".join(f"- {p}" for p in plan) + f"""

## 執行結果
```json
{json.dumps(observations['findings'], ensure_ascii=False, indent=2)}
```

## 評估
- 成功完成一次完整閉環
- 未觸及任何高風險動作
- 紀錄已寫入伏藏

## 反思
千手秘已開始動起來。下一步可擴大到真實外部低風險網路任務（例如讀取公開頁面狀態）。
"""
    log_path = write_observation("T-001", md)

    # 4. Update task
    task["status"] = "done"
    task.setdefault("history", []).append({
        "event": "completed",
        "by": "yingrufeng",
        "note": f"第一次閉環完成，觀察紀錄寫入 {log_path}",
        "at": now()
    })
    task["completed_at"] = now()
    task["observation_path"] = log_path

    save_board(board)

    return {
        "status": "done",
        "observation": log_path,
        "findings": observations["findings"]
    }

if __name__ == "__main__":
    result = run_t001()
    print(json.dumps(result, ensure_ascii=False, indent=2))
