"""P1E capability-scoped load-aware scheduling and recovery decisions."""
from dataclasses import dataclass
from p1d_routing import TaskRequirement, BodyProfile

@dataclass
class CapabilityLoad:
    agent: int = 0; agent_capacity: int = 1
    compute: int = 0; compute_capacity: int = 0
    agent_available: bool = True; compute_available: bool = True

def choose_agent(req: TaskRequirement, bodies: list[BodyProfile], loads: dict[str, CapabilityLoad]):
    qualified = [b for b in bodies if not b.affinity_reasons(req)]
    rejected = {b.body_id: b.affinity_reasons(req) for b in bodies if b.affinity_reasons(req)}
    available = [b for b in qualified if loads[b.body_id].agent_available and loads[b.body_id].agent < loads[b.body_id].agent_capacity]
    if not available: return {"decision":"WAITING_RETRY", "reason":"AGENT_UNAVAILABLE_OR_BUSY", "rejections":rejected}
    b = min(available, key=lambda x:(loads[x.body_id].agent/loads[x.body_id].agent_capacity, x.body_id))
    return {"decision":"DISPATCH", "body_id":b.body_id, "rejections":rejected}

def choose_compute(caller: BodyProfile, req: TaskRequirement, loads: dict[str, CapabilityLoad]):
    if not req.needs_model: return {"decision":"NO_COMPUTE_REQUIRED"}
    if caller.body_id == "office-4090" and caller.has_local_compute:
        load=loads[caller.body_id]
        if load.compute_available and load.compute < load.compute_capacity: return {"decision":"LOCAL_COMPUTE", "body_id":caller.body_id}
        return {"decision":"COMPUTE_UNAVAILABLE", "reason":"LOCAL_COMPUTE_BUSY_OR_CAPACITY"}
    office=loads.get("office-4090")
    if office and office.compute_available and office.compute < office.compute_capacity:
        office.compute += 1
        return {"decision":"REMOTE_COMPUTE", "body_id":"office-4090", "port":11434}
    return {"decision":"COMPUTE_UNAVAILABLE", "reason":"OFFICE_4090_COMPUTE_BUSY_OR_UNAVAILABLE"}
