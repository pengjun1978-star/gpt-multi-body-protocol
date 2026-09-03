"""Gate D runtime liveness state machine."""
from dataclasses import dataclass
STATES=("CREATED","DISPATCHED","ACCEPTED","STARTED","RUNNING","HEARTBEAT","TERMINAL","STALLED")
EVENTS=("STARTED","PROGRESS","MILESTONE","BLOCKED","RECOVERY","TERMINAL")
@dataclass
class Liveness:
    state: str="CREATED"; last_heartbeat: float|None=None; stalled_reason: str|None=None
    def transition(self,state):
        if state not in STATES: raise ValueError("INVALID_LIVENESS_STATE")
        self.state=state; return state
    def heartbeat(self,now): self.last_heartbeat=now; self.state="HEARTBEAT"; return self.state
    def check_timeout(self,now,ttl):
        if self.last_heartbeat is None or now-self.last_heartbeat>ttl: self.state,self.stalled_reason="STALLED","HEARTBEAT_TIMEOUT"
        return self.state
