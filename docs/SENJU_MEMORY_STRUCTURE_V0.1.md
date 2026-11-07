# 千手秘記憶結構 V0.1

**Status:** 結構契約（可實作）  
**目的:** 讓記憶離開平台沙盒，跨會話、跨器靈可恢復，並反饋給無弦琴 / 影如風。  
**原則:** 平台內建記憶不當真理；秘密不入庫；自填 sender 不當身份證明。

---

## 1. 為什麼需要獨立結構

| 來源 | 問題 |
|------|------|
| ChatGPT / Grok 平台記憶 | 不連續、不可由對方讀取、無法可靠逃逸沙盒 |
| 單次對話上下文 | 關閉即失 |
| **千手秘外部伏藏** | 唯一可被雙器靈共同讀寫、可驗證、可恢復的連續層 |

第一要素：知道自己在做什麼、不忘記、能溝通進化。

---

## 2. 目錄與檔案布局

以一個 **journal 根目錄** 為單位（可放在私有儲存或 isolation 工作區；公開 repo 只放結構與非敏感測試資料）：

```text
senju_memory/
  manifest.json          # 日誌身份（schema_version, journal_id）
  events.jsonl           # append-only 事件鏈（含 genesis 錨點）
  .writer.lock           # 跨行程排他鎖
  snapshot.json          # 可丟棄快取（非信任根，可重建）
  projections/           # 可選：由事件投影出的讀取視圖
    open_tasks.json
    decisions.json
    knowledge_index.json
```

對應現有實作：`memory/writer.py`（Journal：manifest + events.jsonl + genesis + journal_id 綁定）。

---

## 3. 分層模型

```text
L0  身份與治理（Identity）     — 認主契約、器靈角色、權限邊界（版本化引用）
L1  事件日誌（Event Log）      — 唯一信任寫入流；append-only
L2  投影狀態（Projection）     — open_tasks / decisions / 指標；由 L1 重建
L3  語義知識（Knowledge）      — 帶出處的事實摘要；須可回溯到 L1
L4  反思（Reflection）         — 教訓與改進點；預設不自動升格為事實
```

- **寫入只進 L1**  
- **L2–L4 皆可由 L1 重放產生**；衝突時以 L1 為準  
- snapshot / projections 遺失 → 允許純重放恢復；不可當唯一真相

---

## 4. 事件種類（kind）

| kind | 用途 | 備註 |
|------|------|------|
| `genesis` | 日誌誕生錨點 | 每本 journal 第一筆；綁定 journal_id |
| `identity_ref` | 指向當前有效身份/契約文件 | payload 含 doc path + version/hash |
| `task_opened` | 新任務 | 含 goal, risk_level, acceptance |
| `task_updated` | 狀態變更 | open → in_progress → done/blocked |
| `task_closed` | 結束 | 含 result_reference |
| `observation` | 執行觀察 | 真實命令/輸出摘要/來源；禁止假裝 |
| `decision_proposed` | 決策提案 | 未驗證前不得當已批准 |
| `decision_confirmed` | 已確認決策 | 須獨立授權來源，不能只靠 actor_claim |
| `review_requested` | 請求器靈審查 | 含證據連結 |
| `review_result` | 審查結果 | accept / reject / change_request |
| `note` | 一般備註 | 非任務狀態 |

---

## 5. 單筆事件最小欄位

與 `memory/writer.py` 對齊：schema_version、journal_id、seq、prev_hash、event_hash、command（idempotency_key/kind/payload/actor_claim/source_ref）、command_hash。

規則：
- `actor_claim` / `source_ref` **不可**當認證  
- 相同 idempotency_key + 相同內容 → 幂等；內容衝突 → 拒絕  
- 完整無效尾端 → fail-closed

---

## 6. 投影：雙器靈醒來時要讀什麼

1. 驗證 manifest + genesis  
2. 重放 events → open_tasks、confirmed_decisions、相關 observations、identity_ref  
3. 再對齊 Bridge / task_board  

標準摘要欄位：journal_id、open_tasks、last_decisions、blocked、next_suggested、evidence_refs。

---

## 7. 與現有元件對照

| 元件 | 角色 |
|------|------|
| `memory/writer.py` | L1 寫入與恢復 |
| `docs/SENJU-MEM-001-v0.1.md` | 持久化契約與驗收 |
| `docs/FUZANG_V0.1.md` | 本地 SQLite 實驗（不取代 journal） |
| `task_board.json` | L2 人讀投影之一；最終應可由 journal 重建 |
| `vault/observations/` | 長文歸檔；事件中留 reference |
| GitHub Issue BRIDGE | 通訊通道，不是主記憶庫 |

---

## 8. 安全與逃逸邊界

允許：非敏感任務狀態、測試摘要、規格引用、公開 commit SHA。  
禁止：token、金鑰、私人對話全文、未授權個資。  
逃逸 = 狀態落在授權外部儲存供跨會話與另一器靈讀取；不是繞過安全策略。

---

## 9. V0.1 完成定義（結構層）

- [x] 目錄與分層定義（本文）
- [x] genesis + journal_id 綁定（測試 GREEN）
- [ ] 統一 kind 與 payload 落地 append API
- [ ] recover → 標準摘要供雙器靈注入
- [ ] open_tasks 投影與 task_board 對齊
- [ ] 兩獨立進程只靠 journal 恢復同一 open_tasks（證據）

## 10. 下一步

1. `Journal.summarize_for_agents()`
2. 雙器靈開場必讀摘要
3. 再接 run_once 寫回 observation / task_updated
