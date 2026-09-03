"""P1D affinity-first Agent and Compute routing primitives."""
from dataclasses import dataclass, field

@dataclass(frozen=True)
class TaskRequirement:
    task_id: str
    responsibility: str
    data_owner: str
    os: str | None = None
    hardware: str | None = None
    environment: str | None = None
    permissions: frozenset[str] = frozenset()
    needs_model: bool = False
    model: str | None = None

@dataclass
class BodyProfile:
    body_id: str
    responsibilities: frozenset[str]
    data_owners: frozenset[str]
    os: str
    hardware: str
    environments: frozenset[str]
    permissions: frozenset[str]
    agent_load: int = 0
    agent_capacity: int = 1
    compute_load: int = 0
    compute_capacity: int = 0
    state: str = "AVAILABLE"
    has_local_compute: bool = False
    def affinity_reasons(self, req):
        reasons=[]
        if req.responsibility not in self.responsibilities: reasons.append("responsibility")
        if req.data_owner not in self.data_owners: reasons.append("data_owner")
        if req.os and req.os != self.os: reasons.append("os")
        if req.hardware and req.hardware != self.hardware: reasons.append("hardware")
        if req.environment and req.environment not in self.environments: reasons.append("environment")
        if not req.permissions <= self.permissions: reasons.append("permissions")
        if self.state != "AVAILABLE": reasons.append("state")
        return reasons

class BodyAffinitySelector:
    def select(self, req, bodies):
        qualified=[b for b in bodies if not b.affinity_reasons(req)]
        rejected={b.body_id:b.affinity_reasons(req) for b in bodies if b.affinity_reasons(req)}
        if not qualified: return None, rejected
        chosen=min(qualified, key=lambda b:(b.agent_load/b.agent_capacity if b.agent_capacity else 999, b.agent_load, b.body_id))
        return chosen, rejected

class AgentScheduler:
    def __init__(self, selector=None): self.selector=selector or BodyAffinitySelector()
    def schedule(self, req, bodies):
        body, rejected=self.selector.select(req,bodies)
        if body is None: return {"decision":"REJECT","rejections":rejected}
        if body.agent_load >= body.agent_capacity: return {"decision":"REJECT","reason":"AGENT_CAPACITY","body_id":body.body_id,"rejections":rejected}
        body.agent_load += 1
        return {"decision":"DISPATCH","body_id":body.body_id,"rejections":rejected}

class ComputeRouter:
    def route(self, req, body, available_models):
        if not req.needs_model: return {"decision":"NO_COMPUTE_REQUIRED","body_id":body.body_id}
        if body.has_local_compute and req.model in available_models:
            body.compute_load += 1
            return {"decision":"LOCAL_COMPUTE","body_id":body.body_id,"model":req.model,"port":None}
        if body.body_id == "mbp-primary" and req.model in available_models:
            return {"decision":"REMOTE_COMPUTE","body_id":"office-4090","model":req.model,"port":11434}
        return {"decision":"REJECT","reason":"MODEL_OR_COMPUTE_UNAVAILABLE","body_id":body.body_id}
