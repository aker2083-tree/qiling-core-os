# SENJU-MEM-CORE-001 — Cross-session shared memory contract (V0.1)

Status: design + test target; **not** a claim of deployed cross-platform continuity.
Parent: SENJU-MEM-001 / BRIDGE-001.
Core agents: wuxianqin/openai and yingrufeng/grok. SENJU is external storage and orchestration, not a third reasoning persona.

## Objective
After both model sessions end and the worker restarts in a fresh environment, a newly authorized session can retrieve the same task state, verify its provenance, resume at the next incomplete step, and append a new result without replaying a completed side effect.

## Trust and authorization
- Platform-supplied authenticated principal is distinct from an untrusted `actor_claim` or self-declared `sender`.
- Each write includes an authenticated source record, model/tool origin, task ID, event ID, correlation/reply-to ID, source URL/commit SHA, UTC server timestamp, schema version, and payload digest.
- Never treat a GitHub comment's `sender` text as proof of the model that generated it.
- API credentials and authorization policy live outside the model-editable memory store.
- Memory is retrieved only through authorized APIs; no sandbox bypass, secret exposure, or privilege escalation.

## Logical data model
1. Immutable event journal: task_created, proposal_added, review_added, decision_recorded, execution_requested, execution_observed, reflection_added, task_completed.
2. Derived task snapshot: task_id, goal, constraints, last_confirmed_event, pending_steps, approvals, code_refs, evidence_refs, next_action.
3. Retrieval index: search by task_id, agent, topic, timestamp and source; all retrieved snippets carry provenance.
4. Recovery checkpoint: journal identity, last verified sequence/hash, snapshot version, last applied event IDs.
5. Skill registry (later): authorized tool names, required approvals, invocation/result schemas, evidence.

## Minimum API contract (future Vercel implementation)
- POST /api/memory/events: validate authenticated principal, schema, idempotency key, allowed event transition; append once.
- GET /api/memory/tasks/{task_id}: return verified snapshot and provenance references.
- GET /api/memory/context?task_id=...: return bounded relevant memory with citations and unresolved questions.
- POST /api/memory/recover: verify journal and rebuild snapshot; refuse tampered or missing history.
These endpoints are design targets, **not currently deployed**.

## Recovery acceptance test
1. Agent A creates task and appends proposal; persist to external durable storage.
2. Agent B independently fetches that task, records review with its verified origin.
3. Persist a decision and next_action, then terminate the worker/session.
4. Recreate the worker in a fresh environment against the same authorized storage.
5. Verify journal integrity, retrieve task, reconstruct decision and next_action.
6. Re-submit a previously committed event ID: no duplicate side effect.
7. Submit a conflicting event with the same idempotency key: reject.
8. Tamper with journal identity, event payload, or provenance: fail closed.
9. Append a new event from the resumed session and verify another fresh restart sees it.

## Current verified vs missing
- Existing `memory/writer.py` supports local POSIX append/recover with hash chain and idempotency, not cloud-native multi-host atomic writes.
- Shared durable database, authenticated API, agent identity verification, context retrieval, independent Grok/GPT execution and end-to-end restart test remain unimplemented or unverified.
- Never mount a local JSONL file on ephemeral Vercel Functions and call it permanent memory.

## Implementation order
A. Add isolated regression tests for deterministic replay, source provenance and conflicting writes.
B. Build storage adapter with transactional append and idempotency in authorized external database.
C. Build read-only context retrieval with source references.
D. Add authenticated API and replay/recovery integration test in separate environments.
E. Integrate dual-agent task handoff; then enable bounded tool orchestration.

## Boundaries
No auto-merge, production deployment, secret reads, model self-modification, or bypass of platform security. Any external side-effect tool requires separate authorization and audit.
