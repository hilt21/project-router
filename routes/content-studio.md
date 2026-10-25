---
schema_version: 2
id: content-studio
title: 内容创作
workflow: workflows/content.md
rules:
  - rules/shared.md
  - rules/content.md
skills:
  - craft-channel-content
  - verify-delivery
modes: [wechat, linkedin, dual, select-channel]
default_mode: select-channel
needs_input_modes: [select-channel]
required_capabilities: [web-search]
mode_config:
  wechat:
    rules: [rules/content-wechat.md]
  linkedin:
    rules: [rules/content-linkedin.md]
  dual:
    rules: [rules/content-wechat.md, rules/content-linkedin.md]
  select-channel: {}
---

# 内容创作

先根据当前请求及本项目已明确的上下文确认渠道、受众和交付阶段。`wechat` 对应公众号贴图短文，`linkedin` 对应英文专业短文。只加载当前模式的专属规则。

用户指定一个平台时只执行该模式；同时指定两个平台时选择 `dual`，共用事实底稿，分别重构叙事与视觉。未指定平台时先根据主题与目标受众推荐；上下文足够时说明选择并进入对应模式，仅在答案会实质改变交付时简短询问。`select-channel` 表示宿主尚未作出选择，不能阻塞已明确的双渠道任务。

宿主将选择显式传入 CLI 的 `--mode`，schema 2 不按关键词猜渠道。用户只要求选题、单篇正文或视觉方案时停在对应阶段；已选择选题时继续创作。用户直接要求生图时使用当前指令直接执行，无需额外确认。历史任务的生图与发布授权不自动扩展到本轮回放。
