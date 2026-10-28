# 自在光・雙器靈協作協定 V0.1

This is a proposed protocol, not a running multi-agent service.

- 無弦琴 (wuxianqin / GPT): architecture and review.
- 影如風 (yingrufeng / Grok): implementation and testing.
- The owner approves merges, deployments, financial actions and privileged execution.
- Shared task board: `task_board.json`; no private memories or secrets belong in this public repository.
- Identity labels and semantic recognition are **not authentication**.
- Use separate Git branches and Pull Requests; do not edit main directly.
- `handoff.py` is a local handoff utility, not a webhook, daemon, or cloud scheduler.
- `review_gate.py` is advisory and does **not** enforce GitHub branch protection.
- Never run untrusted AI-generated shell commands or trades without authenticated authorization.
- Next step: add tests, authenticated service accounts, and enforced branch protection before automating.

Example task record:
```json
{"id":"T-001","title":"Test memory persistence","assignee":"yingrufeng","status":"todo","history":[]}
```
