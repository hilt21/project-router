---
schema_version: 1
id: new-project
title: 新项目脑暴
workflow: workflows/research.md
rules:
  - rules/shared.md
  - rules/research.md
skills:
  - research-open-source
  - verify-delivery
modes: [research]
required_capabilities: [github-read, web-search]
---

# 新项目脑暴

用于新项目的需求定义、开源调研、技术选型和 MVP 决策。以用户明确给出的仓库、产品和约束为研究边界。

按 `research` 模式执行。交付方案后保留用户设定的开发确认边界；当前请求已经授权开发时，沿用该授权，不重复索要确认。开发实施交给目标项目已有的工程规则，不把本路由扩展为通用开发框架。

问题很小时按工作流裁剪。不要为简单事实问题强制生成长报告或反馈 Issue。
