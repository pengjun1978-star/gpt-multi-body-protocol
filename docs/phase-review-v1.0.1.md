---
title: GPT与本地Codex协同工作
date: 2026-09-02
type: project_review
tags:
  - GPT
  - Codex
  - Multi-Body
  - GPT-Multi-Body-Protocol
  - 阶段复盘
status: v1.0.1 GPT_ACCEPTED/PASS
---

# GPT Multi-Body Protocol 阶段复盘

## 一、结构化交接

### 完成任务

- 完成 GPT Multi-Body Protocol v1.0 frozen baseline 的架构与协议设计。
- 完成 v1.0.1 Production Hardening：心跳、租约、健康评估、故障恢复、安装与回滚模板、Body Self-Identification 和时钟偏差证据要求。
- 完成 `control-attempt20-final-heartbeat-pipeline-e2e` 真实双机故障链验证。
- GPT 已对 attempt20 作出 `GPT_ACCEPTED / PASS` 验收。
- 当前阶段复盘文档已导出；GitHub 发布仍需先补齐并确认 v1.0 冻结 tag/release 边界。

### 核心结论

项目已从协同概念推进到可验收的多硬件执行协议：GPT 是唯一 Brain，Codex 绑定实体硬件作为 Body；Body 执行并提交证据，GPT 负责最终验收、记忆提交和全局完成判断。

attempt20 已验证完整链路：

```text
ONLINE → heartbeat 停止 → STALE → ORPHANED → watchdog 自动恢复 → ONLINE
```

恢复后 `supervisor_count=1`、`worker_count=1`，连续心跳推进，无 PID storm，`side_effect_state=NONE`。

### 已确认信息

| 项目 | 当前状态 |
| --- | --- |
| GPT Brain | 统一决策、规划、路由、验收与记忆权威 |
| MacBook Pro Codex | PRIMARY / ACTIVE / CONTROL；`mbp-primary` |
| Office-4090 Codex | EXTENSION / ACTIVE / EXECUTION；Windows 11、i9-14900KF、RTX 4090 |
| Mac Studio Codex | RESERVED；`routing=false`，尚未接入生产网络 |
| v1.0 | GPT_ACCEPTED / FROZEN baseline |
| v1.0.1 | GPT_ACCEPTED / PASS；Production Hardening 完成 |
| attempt20 | 独立 live fault request，Office consumer 自动消费并完成 watchdog 恢复 |
| 当前 GitHub 状态 | remote 已确认；远端当前仅见 `main`，未见 `v1.0` tag |

### 未解决问题

- Office health 文件输出 raw `ACTIVE`；`STALE/ORPHANED` 由 Mac CONTROL 按 heartbeat age/lease 阈值独立推导。
- `STALE` 与 `ORPHANED` 的精确转换时刻受采样间隔约束，Office runtime 尚未序列化。
- v1.0.1 尚未安全发布到 GitHub。当前仓库与 v1.0.1 工作区分离，且远端缺少可核验的 v1.0 tag/release。

### 下一步建议

1. 由 GPT/项目维护者确认：`817c16a` 是否正式代表 v1.0 frozen baseline，是否允许以该提交补建不可变 `v1.0` tag/release。
2. 将已验收的 v1.0.1 工作区整理为公开仓库内容，清除 receipts、绝对路径、机器私有信息、网络标识与缓存文件。
3. 更新 README、CHANGELOG、版本资料，先做安全审计与完整 diff 检查，再创建 `v1.0.1` tag/release；保留 v1.0 不变。
4. 进入 v1.1 Task Routing & Capability Registry：能力注册、任务路由、资源/风险约束、幂等键、回调与验收状态机。
5. 以真实业务接入作为验证路线：本地知识库归档、企业邮箱、充电运营数据、文档处理、GPU 推理和跨硬件批处理；每条路线保留可追溯 Receipt。

### 涉及实体与关键数据

- 仓库 remote：`https://github.com/pengjun1978-star/gpt-multi-body-protocol.git`
- v1.0 baseline 本地提交：`817c16a`（需确认是否为正式冻结锚点）
- v1.0.1 验收任务：`20260902-office4090-v101-hardening-01`
- 最终控制验证：`control-attempt20-final-heartbeat-pipeline-e2e`
- 最终 receipt：`referenced-chatgpt-conversation-this-is-an-15/outputs/gpt-multi-body-protocol-v1.0.1/receipts/control-validation-office-4090-attempt20-final.json`
- 最终 receipt 状态：`PASS_PENDING_GPT_ACCEPTANCE`；GPT 已在上级对话中验收为 `GPT_ACCEPTED / PASS`

## 二、全量内容归档

### 1. 项目定位与架构

项目目标是建立以 GPT 为唯一 Brain、多个 Codex 与多台实体计算机作为 Body 的个人/企业 AI 执行网络。GPT 负责理解目标、形成方案、拆解任务、选择 Body、下发任务、验收 Receipt，并决定下一步。Codex Body 负责本机执行、证据记录和结果回传。

```text
用户
  ↓
GPT Brain：决策 / 规划 / 路由 / 验收 / 记忆
  ↓
MacBook Pro：PRIMARY / CONTROL
  ├─ Office-4090：EXTENSION / EXECUTION
  └─ Mac Studio：RESERVED / routing=false
```

Body 不能自行宣布全局成功。执行完成最多进入 `PASS_PENDING_GPT_ACCEPTANCE`，最终状态由 GPT 置为 `GPT_ACCEPTED / PASS`。

### 2. v1.0 frozen baseline

v1.0 定义 Task Envelope V2、Execution Receipt V2、GPT Verdict/Acceptance Gate、Heartbeat/Lease、Recovery/Retry/Reroute、Callback Contract、Continuous Task Context Inheritance 与 Bootstrap 等协议表面。v1.0 作为冻结架构参考，后续生产守护进程、调度、故障转移和新硬件接入进入增量版本。

### 3. v1.0.1 Production Hardening

v1.0.1 增加 resident heartbeat daemon、原子状态写入、信号安全停止、macOS LaunchAgent、Windows Scheduled Task、控制面健康评估、安装/修复/禁用模板、可回滚路径和结构化验证 Receipt。

新增 Body Self-Identification 强制前置：hostname、OS/platform、CPU 架构、适用 GPU、节点/注册表身份和可安全读取的网络身份必须与 registry 匹配，否则停止并返回 `BODY_MISMATCH`。新输出使用 `Asia/Shanghai` 与显式 `+08:00`；年龄、租约 TTL、时钟偏差使用 epoch/UTC instant；旧 v1.0 `Z` 时间戳继续兼容。

### 4. attempt20 最终验证

Mac CONTROL 发出全新的 live、single-use、test-only `heartbeat_pipeline_stop` 请求，目标为 Office-4090。Office consumer 自动消费请求，由 Office 本地 handler 根据 runtime PID state 停止 supervisor 与 worker。Mac 独立观察到 heartbeat 停止，按 heartbeat age/lease 阈值推导 `STALE → ORPHANED`；watchdog 自动重启 supervisor 与 worker，heartbeat 恢复并连续推进。

验证结果包含：Body Self-Identification、唯一 live request、既有 inbox 投递、Office 自动消费、handler `executed=true`、心跳停止与恢复、watchdog recovery、恢复后单 supervisor/worker、无 PID storm、`side_effect_state=NONE`，以及没有错误宣布 `COMPLETED/PASS`。

最终上级 GPT 验收结论：`v1.0 = GPT_ACCEPTED / FROZEN / 已发布`；`v1.0.1 = GPT_ACCEPTED / PASS / Production Hardening 完成`。v1.0.1 尚未发布 GitHub。

### 5. 当前限制与发布边界

Office health 文件目前只输出 raw `ACTIVE`，控制层根据采样与 lease 窗口推导状态；精确转换时刻尚未由 Office 序列化。该限制不阻塞 v1.0.1 的协议验收，后续可作为可观测性增强项。

本次发布前审计发现：v1.0.1 工作区不是 Git 仓库；现有 Git 仓库位于 `referenced-chatgpt-conversation-this-is-an-14/outputs/gpt-multi-body-protocol`，本地 HEAD 为 `817c16a`，remote 为上述 GitHub 地址，远端仅返回 `main`，没有 v1.0 tag。由于无法从 Git 证据确认正式冻结 tag 边界，发布动作暂停。

### 6. 后续路线图

v1.1 聚焦 Task Routing & Capability Registry：建立 Body 能力登记、路由约束、资源与风险判断、任务幂等、回调状态机、Receipt 规范和可观测性。完成协议层后接入真实业务，优先选择可验证、可回滚、边界清晰的知识库归档、企业邮箱、充电运营数据、文档处理、GPU 推理与批处理任务。

---

来源：当前用户提供的《GPT与本地Codex协同工作》对话预览、MacBook Pro 本地仓库审计、v1.0.1 验收 Receipt。
