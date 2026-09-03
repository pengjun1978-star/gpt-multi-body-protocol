"""Explicit v1.1.1 task resource contract."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ResourceContract:
    execution_requirement: str
    compute_requirement: str="none"
    data_requirement: str=""
    artifact_requirement: str=""
    callback_requirement: str=""
    recovery_policy: str="exact_resume"
    execution_placement: str|None=None
    compute_placement: str|None=None
    def validate(self):
        fields=("execution_requirement","compute_requirement","data_requirement","artifact_requirement","callback_requirement","recovery_policy")
        if any(not getattr(self,f).strip() for f in fields): raise ValueError("RESOURCE_CONTRACT_INCOMPLETE")
        return True
