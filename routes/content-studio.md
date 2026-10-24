---
schema_version: 1
id: content-studio
title: 内容创作
workflow: workflows/content.md
rules:
  - rules/shared.md
  - rules/content.md
skills:
  - craft-channel-content
  - verify-delivery
modes: [wechat, linkedin, select-channel]
required_capabilities: [web-search]
---

# 内容创作

先根据当前请求及本项目已明确的上下文确认发布渠道。`wechat` 对应公众号贴图短文，`linkedin` 对应英文行业短文。

未明确渠道，或要求同时处理两个渠道时，使用 `select-channel`。只补充一个必要的渠道问题；已明确需要双渠道时直接拆成两个独立子任务，分别加载本路由的两种模式。不要把两种语言、篇幅和视觉方案混成一个产物。

用户只要求选题时先交选题；已选择选题时继续创作；已授权生图时检查生图工具并执行。历史会话中的发布授权不能自动用于本次任务。
