---
schema_version: 2
id: academic-research
title: 学术研究与投稿准备
workflow: workflows/academic.md
rules: [rules/shared.md, rules/academic.md]
skills: [verify-delivery]
modes: [select-stage, scope, literature, math, experiment, write, review, submission, pipeline]
default_mode: select-stage
needs_input_modes: [select-stage]
required_capabilities: [github-read]
mode_config:
  select-stage: {}
  scope:
    skills: [scope-academic-research]
    optional_capabilities: [web-search]
  literature:
    skills: [build-literature-evidence]
    optional_capabilities: [artifact-read]
  math:
    skills: [audit-mathematical-rigor]
    optional_capabilities: [artifact-read, code-execution]
  experiment:
    skills: [validate-research-experiments]
    optional_capabilities: [artifact-read, code-execution]
  write:
    skills: [write-academic-manuscript]
    optional_capabilities: [artifact-read, code-execution, web-search]
  review:
    skills: [review-academic-manuscript]
    optional_capabilities: [artifact-read, code-execution, web-search]
  submission:
    skills: [audit-publication-readiness]
    required_capabilities: [web-search]
    optional_capabilities: [artifact-read, code-execution]
  pipeline:
    optional_capabilities: [web-search, artifact-read, code-execution]
---

# 学术研究

支持工程理论、建模、实验、仿真、文献研究、论文写作与投稿准备。按当前请求选择单阶段；只有用户明确要求完整流程时使用 pipeline。

宿主依据明确意图选择 mode，例如检查推导进入 math，核对引用进入 literature，回应审稿意见进入 review。明确阶段缺少输入时，保留该阶段并盘点缺口。没有可确定意图时使用 select-stage；已有上下文足够时不重复追问。

CLI 通过 --mode 接受宿主选择，不猜测科研阶段。每次只加载公共依赖与所选阶段的 skill。pipeline 首先盘点材料和下一阶段，再以同一工作流 SHA 加载需要的阶段；不能声称已经读过全部 skills。
