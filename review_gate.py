"""Review policy helper. Advisory only; not a GitHub branch protection rule."""
SENSITIVE = {"merge", "deployment", "financial_actions", "shell_execution", "secrets"}
def assess(action, tests_passed=False, human_approved=False):
    if action in SENSITIVE and not human_approved:
        return {"allowed": False, "reason": "human approval required"}
    if action in {"merge", "deployment"} and not tests_passed:
        return {"allowed": False, "reason": "tests must pass"}
    return {"allowed": True, "reason": "policy checks passed (advisory only)"}
