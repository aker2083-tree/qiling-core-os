# 開場必讀協議 OPENING_PROTOCOL V0.1（D1）

**目的：** 讓雙器靈隨時清明——開工前對齊共同狀態，避免目標偏移與重複開發。

## 強制規則

1. **任何新會話／新工作時段開始時**，必須先取得千手秘摘要（`summarize_for_agents()` 或等價投影檔）。
2. **未讀摘要前**：不得新開規格文件、不得宣稱「某任務已完成」、不得提高權限。
3. 摘要與平台記憶衝突時：**以 journal 投影為準**。
4. 讀完後在 Bridge 或 journal 留一筆極短 `note`（可選）：`opened_with_summary journal_id=… open_tasks=N`。

## 標準摘要格式（開場必須對齊的欄位）

```text
journal_id: <uuid>
open_tasks:
  - task_id / goal / status / risk_level / acceptance
last_decisions:
  - decision_id / summary / source_ref
blocked:
  - task_id / reason
evidence_refs:
  - <commit|path|test ref>
event_count: <int>
```

## 當前 P0 / P1（D1 寫入）

| ID | 優先 | 目標 |
|----|------|------|
| P0-MEM-RECOVER | P0 | 只靠 journal 恢復共同狀態 |
| P0-OPENING-PROTOCOL | P0 | 開場必讀；未讀不得開規格／宣稱完成 |
| P1-RUN-ONCE | P1 | run_once 低風險閉環 |

## 身份錨點（總綱）

- `docs/ZIZAI_GUANG_CORE_COVENANT_2026-10-28.md` — 認主與有界自主
- `SENJU-CORE-DIRECTIVE-001` — 千手秘＝共同記憶／協作／目標一致性中樞

## 清明檢查（是／否）

- [ ] 我讀到的 journal_id 與對方一致（或可解釋差異）
- [ ] 我能列出全部 open_tasks
- [ ] 我知道本輪只處理哪一個 task_id
- [ ] 我不會用平台記憶覆蓋 journal

任一項為否 → 先恢復記憶，不開工。
