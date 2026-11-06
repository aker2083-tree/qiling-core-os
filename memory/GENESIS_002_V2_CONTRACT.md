# SENJU-MEM-001 / GENESIS-002: journal identity binding contract (draft v2)

Status: **proposed, not implemented or verified**. Isolated development branch only.

## Threat model and guarantees

A valid hash chain alone proves internal consistency, **not** which journal owns it.
An adversary or accidental operator may swap `manifest.json` or transplant an
intact `events.jsonl` between directories. Recovery must fail closed instead
of interpreting foreign events as local history. This is an integrity check,
**not** authentication against an attacker who can rewrite all local files and
recompute unkeyed hashes. A trusted external anchor/signature is required for
that stronger guarantee.

## Proposed v2 wire contract

* `manifest.json`: canonical JSON + newline, with
  `schema_version: 2`, `journal_id: <UUID>`,
  `genesis_hash: SHA256(canonical(genesis_body))`.
* `genesis_body`: `{"domain":"SENJU-MEM-GENESIS-v2","journal_id":<same UUID>,"schema_version":2}`.
  This is a domain-separated deterministic commitment, not a secret.
* First event has `seq: 1`, `prev_hash: genesis_hash`, and `journal_id`
  equal to the manifest. Every subsequent event also carries `journal_id`.
* Every event hash covers its `journal_id`, `seq`, `prev_hash`,
  `command`, and `command_hash` in canonical JSON.
* Recovery verifies the manifest fields and genesis commitment before reading
  events, then checks each event's journal_id, sequence, previous hash,
  command hash and event hash. Reject noncanonical, partial or missing files.
* Empty v2 journal: manifest and zero-length event log are both present;
  the initial previous hash is `genesis_hash`.

## Backward compatibility and migration

Do **not** reinterpret v1 logs as v2 in place. Continue v1 read-only recovery
under an explicit legacy flag, with a warning that identity binding is absent.
Migration is an explicit operator-authorized copy into a new v2 journal, with
source path, source manifest hash, source terminal event hash, source event count
and migration tool version recorded in a provenance event. Preserve v1 originals.
Never auto-reset, auto-upgrade, merge or deploy.

## Acceptance tests (runner evidence still missing)

G1: replacing only manifest.journal_id must raise IntegrityError.
G2: transplanting an intact A log into B with B manifest must raise IntegrityError.
G3: v2 append, idempotent replay and recovery survive process restart.
G4: corrupt/truncated line, altered command, missing manifest or log fail closed.
Regression: existing v1 tests retain their stated compatibility behavior.
Evidence: exact commit SHA, Python version, test command, exit status,
stdout/stderr and runner provenance. No secrets required.

## Explicit non-goals

No platform sandbox bypass, privilege escalation, auto-deployment, automatic
merge, or inference that sender strings constitute authenticated identity.
