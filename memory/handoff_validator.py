"""Read-only, fail-closed handoff graph projection. No identity or authority is inferred."""
def validate_handoff(events):
    accepted, quarantined, seen = [], [], {}
    for source_index, event in enumerate(events):
        if not isinstance(event, dict):
            quarantined.append({"source_index": source_index, "reason": "invalid_event",
                                "verified": False, "authority": None})
            continue
        cmd = event.get("command")
        if not isinstance(cmd, dict):
            quarantined.append({"source_index": source_index,
                                "source_seq": event.get("seq"),
                                "source_hash": event.get("event_hash"),
                                "reason": "invalid_command",
                                "verified": False, "authority": None})
            continue
        if cmd.get("kind") not in ("proposal", "review", "decision_proposed"):
            continue
        payload = cmd.get("payload")
        seq = event.get("seq")
        reason = None
        if not isinstance(payload, dict):
            reason = "invalid_payload"
            payload = {}
        eid, task, parent = payload.get("event_id"), payload.get("task_id"), payload.get("reply_to")
        if reason is None and (not isinstance(eid, str) or not eid or not isinstance(task, str) or not task):
            reason = "invalid_identity"
        elif reason is None and eid in seen:
            reason = "duplicate_event_id"
        elif reason is None and parent is not None:
            if not isinstance(parent, str) or not parent:
                reason = "invalid_parent"
            elif parent not in seen:
                reason = "missing_or_forward_parent"
            elif seen[parent]["task_id"] != task:
                reason = "cross_task_parent"
            elif not seen[parent]["accepted"]:
                reason = "quarantined_parent"
        # Reserve IDs even for quarantined events to avoid laundering later duplicates.
        if isinstance(eid, str) and eid and eid not in seen:
            seen[eid] = {"task_id": task, "accepted": reason is None}
        record = {"event_id": eid, "task_id": task, "reply_to": parent,
                  "source_seq": seq, "source_hash": event.get("event_hash"),
                  "actor_claim": cmd.get("actor_claim"), "verified": False,
                  "authority": None}
        if reason:
            quarantined.append({**record, "source_index": source_index, "reason": reason})
        else:
            accepted.append(record)
    return {"accepted": accepted, "quarantined": quarantined,
            "authorization_granted": False}
