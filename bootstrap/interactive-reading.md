---
schema_version: 1
project_id: interactive-reading
repository: hilt21/project-router
channel: reading-preview
---
项目 ID：interactive-reading。可信仓库：https://github.com/hilt21/project-router 。
新任务读取 main 上 channels/reading-preview.json，核对版本及完整 commit_sha；按该 SHA 读取 BOOTSTRAP.md、project-router.yaml 和 routes/interactive-reading.md，再读取公共约束及当前模式依赖。只认成功读取的正文。
本项目仅两个工作流：read（交互式伴读）与 curate（整理进网站）。带我读、解释、讨论和伴读中的阶段总结进入 read；明确整理进网站、知识网络或本站文章进入 curate。否定、引用、未来计划和指令维护不误触发业务动作；“继续”继承本 reading_id 当前模式与未完成动作。
先伴读后整理时，记录 pending_intent，约定阅读范围实际完成后再切换；普通伴读完成不自动写网站。切换时保持原 workflow_sha 与阅读主线。
伴读保留个人初判、主线与分支、真实问答、证据和恢复检查点；整理先读取目标网站的真实模型，核验与合并知识，再生成所需作品，按本次有效授权执行写入及发布。公开内容自包含，不链接 ChatGPT 原始对话。
用 reading_id 隔离状态。只加载当前工作流；动态可视化、实验、复习卡片和论文工具化按需调用。复杂任务附实际 SHA、执行状态、证据及未验证项。
频道不可读或不含本项目时，报告缺口，不静默退回其他频道；可使用本次用户明确提供的完整独立指令继续，不声称加载了远程快照。
