---
name: capture-router-feedback
description: Capture an observed routing failure, explicit user correction, or verified reusable workflow lesson. Use when evidence supports a focused change; skip routine successes, speculative errors, and automatic global-rule promotion.
---

# 记录路由反馈

读取当前源快照中的 feedback/README.md。区分选错流程、产物质量、工具环境、规则冲突、用户偏好和未知原因。

记录项目 ID、路由 SHA、观察结果、预期结果、脱敏证据、适用范围和可复现输入。缺少证据时先记为待验证观察。

保留直接证据和用户纠正。不要公开完整聊天、凭据、客户信息或其他项目状态。公开写入前按白名单字段脱敏。

默认先在当前对话草拟反馈。只有当前请求或项目长期指令明确授权写入 hilt21/project-router 的反馈时，才使用可用 GitHub 工具创建 Issue。缺少工具时交付可复制正文，不声称已保存。

写入后回读 Issue URL。改进使用小范围候选 PR，附复现案例、反例、旧版与候选版结果、影响范围和回滚方式。合并及推广稳定版本遵循已有授权。

项目纠正保留项目作用域。推广到其他项目需要证据。只有现有产物无法充分保留且值得再次读取的经验，才新增规则。
