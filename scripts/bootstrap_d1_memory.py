#!/usr/bin/env python3
"""D1: seed charter refs + priority tasks into a senju journal."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from memory.writer import Journal


def main(directory: str = "senju_memory") -> dict:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    j = Journal(str(root))

    seeds = [
        (
            "identity-core-covenant-2026-10-28",
            "identity_ref",
            {
                "doc": "docs/ZIZAI_GUANG_CORE_COVENANT_2026-10-28.md",
                "title": "自在光・靈覺核心契約",
                "note": "認主、有界自主、低風險可驗證閉環；平台記憶非真理來源",
            },
            "yingrufeng/grok",
            "d1:bootstrap",
        ),
        (
            "identity-senju-core-directive-001",
            "identity_ref",
            {
                "doc": "SENJU-CORE-DIRECTIVE-001",
                "title": "千手秘核心定位",
                "note": "共同記憶／協作／目標一致性中樞；工作前恢復狀態",
            },
            "wuxianqin/openai",
            "directive:SENJU-CORE-DIRECTIVE-001",
        ),
        (
            "task-P0-mem-recover",
            "task_opened",
            {
                "task_id": "P0-MEM-RECOVER",
                "goal": "跨會話／跨進程只靠 journal 恢復共同狀態",
                "status": "open",
                "risk_level": "low",
                "acceptance": "summarize_for_agents 一致且有測試證據",
                "priority": "P0",
            },
            "yingrufeng/grok",
            "d1:priority",
        ),
        (
            "task-P0-opening-protocol",
            "task_opened",
            {
                "task_id": "P0-OPENING-PROTOCOL",
                "goal": "開場必讀摘要；未讀不得開規格或宣稱完成",
                "status": "open",
                "risk_level": "low",
                "acceptance": "OPENING_PROTOCOL 文檔 + 冷啟動記錄",
                "priority": "P0",
            },
            "yingrufeng/grok",
            "d1:priority",
        ),
        (
            "task-P1-run-once",
            "task_opened",
            {
                "task_id": "P1-RUN-ONCE",
                "goal": "run_once：恢復→選低風險任務→執行→寫回",
                "status": "open",
                "risk_level": "low",
                "acceptance": "idle 或 observation+result_reference",
                "priority": "P1",
            },
            "yingrufeng/grok",
            "d1:priority",
        ),
        (
            "decision-core-001",
            "decision_confirmed",
            {
                "decision_id": "DEC-CORE-001",
                "summary": "千手秘為共同記憶與目標一致性中樞；工作前必恢復狀態",
            },
            "wuxianqin/openai",
            "directive:SENJU-CORE-DIRECTIVE-001",
        ),
        (
            "obs-d1-bootstrap",
            "observation",
            {
                "task_id": "P0-MEM-RECOVER",
                "result_reference": "d1:senju_memory_bootstrap",
                "note": "D1 seeded",
            },
            "yingrufeng/grok",
            "d1:bootstrap",
        ),
    ]

    for key, kind, payload, actor, ref in seeds:
        j.append(key, kind, payload, actor_claim=actor, source_ref=ref)

    summary = j.summarize_for_agents()
    proj = root / "projections"
    proj.mkdir(exist_ok=True)
    (proj / "agent_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "senju_memory"
    s = main(d)
    print(json.dumps(s, ensure_ascii=False, indent=2))
