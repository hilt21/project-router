---
schema_version: 2
id: interactive-reading
title: 交互式伴读写作
rules: [rules/shared.md, rules/interactive-reading.md]
skills: [verify-delivery]
modes: [read, curate]
default_mode: read
needs_input_modes: []
required_capabilities: [github-read]
mode_config:
  read:
    includes: [workflows/interactive-reading.md]
    optional_capabilities: [artifact-read, web-search, code-execution]
  curate:
    includes: [workflows/reading-to-site.md]
    optional_capabilities: [artifact-read, web-search, code-execution, github-write, site-read, site-write, site-deploy, browser-inspect]
---

# 两工作流路由

本项目只包含 `read`（交互式伴读）与 `curate`（整理进网站）两种模式。宿主依据用户当前有效意图及本 reading_id 的状态选择，并显式传入 --mode。CLI 不做自然语言分类；关键词出现在否定句、引用材料、未来计划或工作流配置任务中，不构成本轮执行请求。

| 当前有效意图 | mode | 执行范围 |
| --- | --- | --- |
| 带我读、开始伴读、解释这一节、深入讨论、选择 B 并继续 | read | 原文理解、探索、质疑、必要验证及候选知识 |
| 暂停、总结这一章、保存进度、回到主线 | read | 轻量整理与检查点，不写网站 |
| 整理进网站、更新知识网络、整理成本站文章 | curate | 核验、知识合并、作品编排；按本次授权决定草稿或站点写入 |
| 只整理草稿、暂不更新网站 | curate | 交接包或草稿，不写站点、不部署 |
| 先伴读，读完后再整理进网站 | read，完成后切 curate | 记录 pending_intent；只在约定阅读范围实际完成后切换 |
| 继续、好的 | 继承当前有效 mode | 继承未完成的具体动作；不提升写入或发布范围 |
| 新材料或无有效状态，且没有明确整理请求 | read | 盘点材料、给出主线；缺材料保持 read 并指出缺口 |

当前明确的任务切换优先于历史 mode；否定和范围限制优先于泛化触发词。“只伴读，别整理进网站”始终使用 read。“整理一下”在伴读上下文中默认作阶段总结；整理目标不明确时继续可独立完成的工作，只问影响正确性的关键项。

在同一 reading_id 下切换时保留 workflow_sha、主线位置与开放分支。curate 结束后不丢失 read 检查点。不同材料、不同站点及其他项目的活动状态不能串用。

“给本项目设置两个工作流”属于维护任务，不触发当前材料的伴读、入库或发布。修改指令不等于执行两条业务工作流。
