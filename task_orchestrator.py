"""Low-resource deterministic multi-task orchestration foundation."""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3


@dataclass(frozen=True)
class Task:
    task_id: str
    priority: Priority = Priority.P2
    dependencies: tuple[str, ...] = ()
    required_capabilities: frozenset[str] = frozenset()


@dataclass
class Body:
    body_id: str
    state: str = "AVAILABLE"
    capabilities: frozenset[str] = frozenset()
    active_task_count: int = 0
    max_concurrency: int = 1

    def can_run(self, task: Task) -> bool:
        return (self.state == "AVAILABLE" and
                self.active_task_count < self.max_concurrency and
                task.required_capabilities <= self.capabilities)


@dataclass
class TaskRegistry:
    tasks: dict[str, Task] = field(default_factory=dict)

    def register(self, task: Task) -> Task:
        if task.task_id in self.tasks and self.tasks[task.task_id] != task:
            raise ValueError(f"TASK_ID_CONFLICT: {task.task_id}")
        self.tasks[task.task_id] = task
        return task


@dataclass
class TaskQueue:
    task_ids: list[str] = field(default_factory=list)

    def enqueue(self, task_id: str) -> None:
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)


class DeterministicScheduler:
    def __init__(self, registry: TaskRegistry, bodies: list[Body], dry_run: bool = True):
        self.registry, self.bodies, self.dry_run = registry, bodies, dry_run

    def schedule(self, completed: set[str] | None = None) -> list[dict[str, Any]]:
        completed = completed or set()
        decisions = []
        for task in sorted(self.registry.tasks.values(), key=lambda t: (t.priority, t.task_id)):
            missing = sorted(set(task.dependencies) - completed)
            if missing:
                decisions.append({"task_id": task.task_id, "decision": "WAIT", "reason": "DEPENDENCY", "missing": missing})
                continue
            body = next((b for b in self.bodies if b.can_run(task)), None)
            if body is None:
                decisions.append({"task_id": task.task_id, "decision": "REJECT", "reason": "NO_AVAILABLE_BODY"})
                continue
            decisions.append({"task_id": task.task_id, "decision": "DRY_RUN" if self.dry_run else "DISPATCH", "body_id": body.body_id})
            if not self.dry_run:
                body.active_task_count += 1
        return decisions
