---
name: design-library
description: Load selected design methods and resources for a configured project stage.
---

# Design Library

固定本任务的 router SHA。读取 `registry/design-library.json`，按项目确认允许的阶段、ID、别名、显式默认值和组合。每阶段限一个条目，未配置默认值时不猜风格。生图另需明确动作和宿主能力。

本包 `index.json` 固定设计库来源 SHA、活动快照目录及文件摘要。读取快照下 `manifests/<id>.json`，再完整读取 `entries/<id>/` 下的入口和 `required` 文件。按任务需要读取 `resources`，CLI 使用 `--design-resource ID=PATH`。执行包只包含选中条目及资源。全部文件沿用原 router SHA。

对照活动索引、条目摘要和 `registry/skills.lock.json`。无法计算摘要时标为未验证。阶段组合也需满足完整执行包预算。条目、文件或能力缺失时报告缺口，暂停依赖动作并继续独立工作。

渠道规范、用户范围、逐图规则和宿主权限继续有效。回执沿用编译结果的 `design_library` 字段并登记已读文件。完成任务还需产物路径及 SHA-256。使用对应的干净 router 提交和产物目录核对回执。静态检查、代理试跑、实际工具运行和人工评审分开记录。
