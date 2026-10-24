---
name: verify-delivery
description: Verify a substantive workflow's delivered result against observable evidence. Use before final delivery of research, content, or project work; skip casual conversation and tiny factual answers.
---

# 交付证据检查

用当前请求的完成条件检查实际产物。按风险选择必要验证，避免为小改动增加无意义步骤。

将证据分为工具回读、产物检查、人工确认、模型自述。仅凭模型自述不能标记通过。缺少证据时记录 unknown 或 not-run。

核对事实来源、数据时间、约束、篇幅、引用和剩余工作。未运行的候选项目保持“未实测”。读取了 skill 只能证明读到了文件，不能单独证明执行正确。

写操作需要成功响应和必要回读。没有工具确认，不能声称文件已保存、Issue 已创建、图像已生成或内容已发布。

先交付结果。复杂任务附紧凑回执：项目 ID、源 SHA、实际已读 skills、验证证据和未验证项。完整机器回执使用源快照中的 templates/receipt.example.json，按 docs/PROTOCOL.md 解释。

出现真实偏差、用户纠正或已验证且可能复发的问题时，再读取 capture-router-feedback。不要用每次运行的自评分替代真实反馈。
