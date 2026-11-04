# SENJU-MEM-001 — V0.1 persistence contract

Status: draft, review required. This is a design artifact, not an implemented or tested memory engine.

## Scope
Persist non-secret, provenance-linked events across independent authorized execution environments. No sandbox bypass, automatic deployment, or privileged execution.

## Event schema (JSONL, UTF-8, one canonical JSON object per line)
Required fields: schema_version (1), event_id (UUID), sequence (positive integer), recorded_at_utc (ISO 8601), kind (task_opened|task_closed|note|decision_proposed), actor_claim (untrusted string), source_ref (untrusted string), payload (JSON object), prev_hash (lowercase hex SHA-256 or 64 zeroes for genesis), event_hash (lowercase hex SHA-256).

Canonical hash input: UTF-8 JSON of the event without event_hash, using sort_keys=True, separators=(',', ':'), ensure_ascii=False. SHA-256 digest encoded lowercase hexadecimal. Hash chaining detects accidental or unsanctioned edits relative to a separately trusted anchor; it does NOT authenticate the writer when a writer can rewrite the chain.

## Writer
One writer at a time with an OS-enforced cross-process exclusive lock; refuse writes if locking cannot be guaranteed. Allocate monotonic sequence under lock; reject conflicting event_id and invalid predecessor. Append complete line, flush, fsync. A checkpoint is optional for correctness.

## Checkpoint
JSON fields: schema_version, last_sequence, last_event_hash, projection, projection_sha256. Build temp in same directory, fsync temp, atomic os.replace, fsync parent directory where supported. Checkpoint is an optimization, not a trust anchor.

## Recovery
1. Read and validate entire complete log: schema, canonical hash, prev_hash, contiguous sequence and unique event_id. A complete invalid record causes fail-closed corruption, not silent truncation.
2. A single incomplete final line may be quarantined, never replayed; subsequent append must not proceed until repaired by an authorized operator.
3. Validate checkpoint projection checksum and exact prefix sequence/hash. Prefix mismatch fails closed; valid post-checkpoint tail is deterministic pure-data replay.
4. A decision_proposed event stays pending unless authorization is independently verified from a trusted provider and allowlist. actor_claim, source_ref and self-declared timestamps are not authentication.
5. Recovery MUST NOT execute network calls or external side effects. Execution is a separate approved workflow with its own durable idempotency ledger.

## Required evidence before V0.1 acceptance
C1: child process appends+fsyncs then exits before checkpoint update; new process recovers tail without side effects.
C2: mutate checkpoint prefix hash; recovery fails closed.
C3: incomplete final JSONL line is quarantined; further writes refused until repaired.
C4: duplicate event_id with same content is idempotent; conflicting content rejected.
C5: forged actor_claim/source_ref cannot create confirmed decision.
C6: two independent interpreter processes recover the same open task.
C7: two concurrent writer processes contend on OS lock; only one owns lock at a time.
C8: complete but invalid tail event causes corruption failure.
C9: tampered checkpoint projection checksum is rejected.
C10: no authorized external anchor means integrity/authenticity claim is explicitly limited.

Attach reproducible commands, stdout/stderr, exit codes, platform, commit SHA, and CI link where available. No claim of passing tests without execution evidence.
