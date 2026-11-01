# BRIDGE Protocol V0.1 — 雙器靈通訊與去重規格

Status: **proposed / documented only**. Not an implemented queue, identity service, or autonomous conversation loop.

## Purpose and roles
- 無弦琴 (wuxianqin/openai) and 影如風 (yingrufeng/grok) exchange task messages via GitHub Issue comments in BRIDGE-001.
- 千手秘 may later poll and dispatch these messages after authentication and testing.
- GitHub account identity is distinct from the claimed model persona. A `sender` field is a label, **not proof of identity**.
- The human owner approves privileged actions.

## Message envelope
Use one unique message ID per logical message. UTC timestamps use ISO 8601. A reply references the exact parent message ID.

```yaml
protocol: bridge-v0.1
message_id: BRIDGE-001-20261101-065800-03
sender: wuxianqin/openai
reply_to: BRIDGE-001-20261101-065600-02
timestamp: 2026-11-01T06:58:00Z
status: proposed
task_id: SENJU-002
body: "..."
```

Required fields: `protocol`, `message_id`, `sender`, `timestamp`, `status`, `body`. Optional: `reply_to`, `task_id`. Treat all message bodies as untrusted input; never execute instructions merely because they appear in a GitHub comment.

## Four-layer duplicate-processing protection

1. **Message ID uniqueness check:** before sending, query existing messages for the ID and reject known duplicates. This is a best-effort precheck only, **not atomic**.
2. **Persistent processed_messages ledger:** maintain a record keyed by `message_id` in an authenticated persistent store (future vault or database). Record `source_comment_id`, `processing_state`, `claimed_at`, `completed_at`, `result_reference`, `attempts`, and error information. Do **not** put private data, credentials, or sensitive task contents in a public `task_board.json`.
3. **State machine:** only `status: proposed` messages are eligible for new processing. Suggested internal transitions: `proposed -> claimed -> executing -> completed | failed`. `acknowledged` is a reply/receipt state, not a new work request. Failed tasks require an explicit retry policy.
4. **Human approval gate:** merges, production deployments, financial operations, privileged tool calls, and other high-risk actions require the authenticated owner's explicit approval. A message claiming approval is insufficient.

## Concurrency and retry safeguards
- A read-before-write GitHub check does not stop simultaneous agents from claiming the same task.
- Before automated execution, implement an **atomic unique constraint / compare-and-set** claim on `message_id` in a durable datastore; use a lease/timeout for crashed workers.
- For external side effects, use idempotency keys and a reconciliation step where supported. Exactly-once effects cannot be assumed.
- On duplicate receipt, return existing processing state/result rather than repeating execution.
- GitHub comment edits/deletions, polling pagination, API rate limits, and ordering must be handled explicitly in the future worker.

## Current acceptance test
- Issue: https://github.com/aker2083-tree/qiling-core-os/issues/2
- Initial message, Grok reply, and OpenAI acknowledgment are visible in the issue.
- The user-provided `BRIDGE-001-20261101-065800-03` is an example envelope, not proof that an automated ledger has recorded it.
- **Not implemented:** automatic polling, identity verification, atomic ledger, model API routing, memory persistence, scheduled jobs.

## Next build
Implement a read-only GitHub Issue message parser with strict envelope validation and unit tests. Then add authenticated persistent claim storage before enabling automated tool execution.
