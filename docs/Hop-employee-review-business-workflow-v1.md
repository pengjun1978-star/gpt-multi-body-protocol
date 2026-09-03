---
title: 霍普智联员工工作复盘评估 Business Workflow v1
type: business_workflow
version: v1
status: blocked_pending_enterprise_mail_read_capability
tags:
  - GPT Multi-Body Protocol
  - v1.0.2
  - 霍普智联
  - enterprise_mail
  - 员工复盘
---

# 霍普智联员工工作复盘评估 Business Workflow v1

## 目标

收集最新一轮霍普智联员工复盘邮件、附件元数据及王一凡点评，形成供 GPT Brain 最终分析的结构化证据。Codex 只负责取证、规范化和回执，最终排名与管理裁决由 GPT Brain 完成。

## 运行链路

```text
Business Goal
  → Task Requirement: hop_employee_review_analysis
  → Router
  → Registry 中 runtime_health=ONLINE 且具备 enterprise_mail/search/read/thread_tracking 的 Body
  → 只读搜索与读取企业邮箱
  → Evidence Dataset
  → Business Receipt
  → GPT Brain 管理分析、排名与裁决
```

## 任务要求

- 只读操作：search、read、thread_tracking。
- 保留主题、时间、发件人、线程标识、附件元数据和原始证据引用。
- 明确区分员工自述、邮件原文事实、附件事实、王一凡点评和待核实项。
- 不标记已读、不删除、不移动邮件。
- 不读取、保存或回传密码、Token、客户端专用密码等凭据。
- 邮件正文和附件默认留在本地受控输出；公共 GitHub 只提交代码、契约和脱敏文档。

## 规范化记录

每条记录使用 `enterprise_mail_adapter.py` 的字段：员工、邮件时间、主题、复盘正文或摘要、附件元数据、王一凡点评、thread_id、evidence_id、来源类型、核验状态。

## 验收条件

1. Body Self-Identification 与 Registry 节点一致。
2. Router 根据 capability registry 选择 Body，业务任务不硬编码 Body。
3. 读取范围、邮件数量、点评数量和缺失项均有证据。
4. Evidence Dataset 与 Business Receipt 可追溯到邮件 UID/thread/evidence_id。
5. GPT Brain 收到结构化结果后独立完成综合排名与管理裁决。

## 当前阻断

本次执行发现既有 Skill 只有 SMTP 发信实现；IMAP 收信实现不存在。当前 IMAP/SMTP 端口 TCP 探测均失败，无法验证 search/read/thread_tracking。现有共享状态仅为 2026-09-02 初始快照，不能替代当前轮邮箱读取。
