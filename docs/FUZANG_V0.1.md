# 伏藏 Fuzang V0.1 — 持久記憶原型

**Status:** local SQLite prototype, not deployed; no cloud database, agent API, semantic retrieval, or automatic reflection yet.

## Existing gap
`qiling_core.py` currently uses a Python list in `Memory.history`; it disappears when the process exits. This prototype is **separate** and does not silently replace or integrate that class.

## Layers
- **Identity**: explicit, versioned persona and governance statements; not cryptographic authentication.
- **Event**: task observations and source links.
- **Semantic**: extracted factual knowledge; requires provenance and validation.
- **Reflection**: critiques and lessons, not automatically accepted as facts.

## Data contract
`id` UUID, `kind`, `agent`, `content`, `source`, `created_at`, `revision`, `superseded_by`. Append-only audit events record creation and revisions. Revisions create a **new** memory and link the previous version, preserving the original. Local text search is substring-based, **not embeddings**. No model-generated conclusions are validated by the database.

## Local usage
```python
from fuzang_store import FuzangStore
store = FuzangStore("local_fuzang.sqlite3")  # local file: do not commit
mid = store.add("event", "wuxianqin", "BRIDGE-001 review completed", "github:issue/2")
print(store.search("BRIDGE-001"))
store.close()
```
A subsequent process opening the same path can read the record. Run tests with `python -m unittest discover -s tests`.

## Security and deployment boundary
- **Do not commit** the SQLite file, personal memories, tokens or private information to a public repository.
- SQLite on a serverless Vercel filesystem is **not** a durable shared cloud store. Use managed PostgreSQL or another durable transactional service before deploying shared writes.
- Future API requires authenticated service identities, owner-scoped authorization, rate limits, encryption, backups, deletion/export, retention policy and audit review.
- GitHub sender strings and semantic owner recognition do not authenticate a caller.
- Concurrent production writes need database constraints and transactions; this local prototype is not a distributed lock or production queue.

## Acceptance criteria for next phase
1. Two separate local processes can save and retrieve the same test record.
2. A revision preserves its predecessor and source.
3. Tests cover invalid types, empty sources, restart persistence, and revision history.
4. Later: deploy a **private** managed database and authenticated API, then run GPT/Grok cross-model read/write tests.
