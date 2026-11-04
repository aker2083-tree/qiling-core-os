# SENJU-001 — 第一項真實工具

## 目的
千手秘以唯讀方式自行向 GitHub Public REST API 查詢自己的專案，回報 open PR 與最近 5 筆 main 分支提交。

## 介面
- GET /api/health：健康檢查
- GET /api/project-status：真正發出 HTTPS 讀取 GitHub API（固定倉庫，不接受任意 URL）
- POST 任意路徑：501，禁止寫入或修改

## 明確未完成
尚未有身份驗證的任務指派、GPT/Grok 自主規劃、伏藏資料庫、跨任務記憶、反思回寫、自我修改或排程。GitHub Public API 有頻率限制，且只能讀公開資料。

## 驗收
1. Preview deployment READY。
2. GET /api/project-status 回傳真實 PR、最近提交及 checked_at。
3. POST 不能修改任何內容。
4. 只有在上述驗證完成後才宣稱 SENJU-001 第一項工具已運作。

## 後續
安全授權 → 任務紀錄與持久化 → 結果評估與反思 → PR 提案機制 → 人工審查合併。
