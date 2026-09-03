# Case 001 重复任务清单与安全处置建议

核验时间：2026-09-03（MacBook Pro Codex）

| 任务标题 | thread_id | 当前状态 | 证据 | 建议 |
|---|---|---|---|---|
| 续跑 Business Case 001 验证 | `01a06521-e6ba-7fd0-baf2-7b84c2d4a877` | idle | Case 001 首个业务执行线；已有业务 receipt/dataset | 作为历史业务执行记录保留，待 GPT 指定 canonical |
| 回传业务证据工件 | `01a06528-0016-7e41-9254-aac5169bcd75` | idle | 回传工件与 hash/visibility 验证 | 可归并为回传阶段历史记录，安全归档 |
| 整理业务证据包并回传 | `01a06529-af3a-7441-9d51-2be636fe934d` | idle | 读取邮件并生成 Evidence Pack | 保留产物，停止后续调度，安全归档 |
| 解析员工复盘附件证据 | `01a0652d-bb1e-7ef3-8951-4ff124a1b2a6` | idle | 23/23 文件提取、Part 1/3–3/3、Manifest | 作为附件证据 canonical candidate，待 GPT 决定后归并 |
| 验证 Business Evidence Receipt | `01a06538-06a5-7d82-b506-256914613f84` | active | v1.0.2 receipt delivery 验证线 | 当前唯一仍 active；先停建新线，完成后按 receipt 归并 |
| 修复任务续跑与防重复机制 | `01a06539-4c9c-7583-bb0c-a9ea15c59238` | active | 本 P0 修复线程 | 保留为 v1.0.2 P0 orchestration defect 修复线 |

## 根因

此前 handoff 接口的实际能力是 `create_thread`，调用方没有先解析 `(parent_gpt_thread_id, task_id)` 映射，也没有验证原 Codex thread/session 是否可恢复；每次“继续”都重新创建了 local Codex thread，并复用了相同业务 `task_id`，形成多条执行记录。完成回执中的业务 task_id 相同，掩盖了 execution thread identifier 已变化的事实。

## 安全处置

只允许在 GPT 明确指定 canonical thread 后，将其他 idle 任务归档或标为 duplicate；先保留所有业务数据和 Evidence Pack。active 任务不自动删除、不强制终止。当前清单仅提供归并建议，未执行不可逆关闭。
