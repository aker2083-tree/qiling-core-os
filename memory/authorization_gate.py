"""Fail-closed planning gate: no executable action without independently verified authority.

SENJU-MEM-001: deliberately does NOT implement approval or execution.
"""
def plan_authorized_actions(projection):
    """Return executable actions; untrusted projection never grants authority.

    Until a separate authenticated, owner-approved capability token verifier exists,
    all events and claimed decisions are audit-only. Never infer authorization from
    event kind, actor_claim, source_ref, or free-text summary.
    """
    return []
