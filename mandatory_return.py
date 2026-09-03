"""Mandatory canonical callback rule for every local Codex terminal state."""
TERMINAL_STATES = frozenset({"COMPLETED", "PARTIAL", "BLOCKED", "FAILED", "CANCELLED"})

class MandatoryReturnError(RuntimeError): pass

def require_parent_return(*, status, parent_route, callback_event_id, sender):
    if status not in TERMINAL_STATES: raise ValueError("NON_TERMINAL_STATUS")
    if not parent_route or not callback_event_id: raise MandatoryReturnError("PARENT_RETURN_REQUIRED")
    try:
        result = sender(parent_route, callback_event_id, status)
    except Exception as exc:
        raise MandatoryReturnError("PARENT_RETURN_FAILED_FALLBACK_ALLOWED") from exc
    if result not in ("SENT", "HOST_ACCEPTED", "UI_VISIBLE", "GPT_ACKED"):
        raise MandatoryReturnError("PARENT_RETURN_NOT_CONFIRMED")
    return result
