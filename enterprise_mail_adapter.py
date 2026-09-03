"""Thin enterprise-mail adapter boundary for Business Case 001.

This module deliberately contains no credential handling. A future IMAP
provider implementation must return normalized evidence without changing the
business task contract.
"""
from dataclasses import dataclass, asdict
from typing import Any


TASK_TYPE = "hop_employee_review_analysis"


@dataclass
class NormalizedMessage:
    employee: str | None
    message_time: str | None
    subject: str | None
    review_body_or_summary: str | None
    attachment_metadata: list[dict[str, Any]]
    wang_yifan_comment: str | None
    thread_id: str | None
    evidence_id: str
    source_kind: str
    verification_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def task_requirement() -> dict[str, Any]:
    return {
        "task_type": TASK_TYPE,
        "goal": "收集最新员工复盘邮件及王一凡点评，形成供 GPT Brain 分析的证据数据集",
        "capabilities": ["enterprise_mail", "mail_search", "mail_read", "thread_tracking"],
        "operations": ["search", "read", "thread_tracking"],
        "read_only": True,
        "include_attachments": True,
        "preferred_body": None,
        "fallback_allowed": False,
    }


def normalize_message(raw: dict[str, Any], evidence_id: str) -> dict[str, Any]:
    """Normalize provider output while preserving employee-vs-fact provenance."""
    item = NormalizedMessage(
        employee=raw.get("employee"),
        message_time=raw.get("message_time"),
        subject=raw.get("subject"),
        review_body_or_summary=raw.get("review_body_or_summary"),
        attachment_metadata=raw.get("attachment_metadata", []),
        wang_yifan_comment=raw.get("wang_yifan_comment"),
        thread_id=raw.get("thread_id"),
        evidence_id=evidence_id,
        source_kind=raw.get("source_kind", "enterprise_mail"),
        verification_status=raw.get("verification_status", "unverified"),
    )
    return item.to_dict()
