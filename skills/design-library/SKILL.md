---
name: design-library
description: Resolve an explicitly selected or route-default design entry for the current content-studio stage.
---

# Design Library

从本任务固定的 `project-router` 源 SHA 读取 `skills/design-library/index.json`。索引的 `commit_sha` 是同步时的设计库来源版本。索引内的路径相对于 `skills/design-library/`，后续文件使用同一 router SHA。

每个阶段最多使用一个主条目。先筛选包含本阶段、且绑定 `content-studio` 的条目，再按用户选择匹配 ID 或别名。也可使用内容工作流明确指定的该阶段默认条目。缺少明确风格的视觉任务沿用既有流程。

完整读取命中条目的入口与声明依赖。对照 `registry/skills.lock.json` 与索引中的对应文件摘要。工具无法计算摘要时，将完整性检查标为未验证。请求的条目、文件或所需能力不可用时，报告具体缺口并暂停依赖它的动作。继续独立工作。

条目只提供方法。渠道规范、用户指定范围、工作流的独立画布规则和宿主权限继续有效。回执记录 router SHA、设计库来源 SHA、命中 ID、阶段和实际读取的文件。
