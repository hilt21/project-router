# 首批来源审阅

日期：2026-10-27。范围：公开收藏元数据及 11 个固定版本的技能入口。机器读取记录见 [source-readings.json](source-readings.json)，条目见 [entries.yaml](../entries.yaml)。

## 实际完成

取得 4 页公开 Starred API 响应，共 306 个不同仓库 ID。54 个来源匹配名称、简介或 topics 中的 skill。保留全部 306 条精简元数据以复核筛选；未逐仓库扫描源码，因此不能把关键词筛选称为完整技能发现。

首批选取 mattpocock/skills 的 to-spec、tdd、retro，obra/superpowers 的 verification-before-completion 和 systematic-debugging，anthropics/skills 的 frontend-design、webapp-testing、doc-coauthoring，以及 humanizer、anatomy 和已有 ARS-Codex 设计参考。每个入口均完整取回，实际内容审阅限于 frontmatter 和正文重点，未对套件作全量审计。

读取了 Matt、Superpowers、Humanizer、Anatomy 的根 LICENSE，以及 Anthropic frontend-design 和 webapp-testing 的各自 LICENSE.txt。条目中的 file-read 只表示该许可证文件已读；未检查全部引用文件的许可证。doc-coauthoring 的许可证保持 unverified。ARS 沿用现有 CC-BY-NC-4.0 来源声明和固定提交，本次未重新完成许可证审计。

本次 Matt 上游为 `5beb35b040e3de97e54fa9e386d7e42d15c295c2`。它与既有 PRD 记录的 curated to-spec 来源分别保存，不能据此把已有 PRD 改标为使用了本次版本。

## 关键适配点

| 来源 | 采用前需要处理 |
| --- | --- |
| to-spec | 上游含发布 Issue 与 ready-for-agent 标签动作；实际授权和目标仓库由宿主判断 |
| tdd / retro | 存在额外技能引用；需读传递依赖并适配本仓库已有反馈边界 |
| Superpowers | 仅储备局部方法；未引入其全局触发、hooks 和整套编排 |
| webapp-testing | 需实际 Python、Playwright、浏览器和服务；长连接页面不能机械等待 networkidle |
| humanizer | 中文效果需验证；保留事实、引用和稳定技术术语 |
| anatomy | 需审阅 kit 与脚本；几何检查和渲染性能不能证明物理模型或工程数据正确 |
| ARS-Codex | 继续关联现有科研阶段规则；数学证明优先使用本地 math 模式 |

## 证据边界

已完成：来源取回、重点审阅、目录关联和明确局限。未完成：全部脚本/网络/传递依赖审计、真实宿主调用、跨 agent 兼容性、效果对照、人工试用验收。host_tests 为空，不能登记 passed。

完整内容未复制进本仓库。读取记录中的 SHA-256 对取回文本的 UTF-8 编码计算；blob SHA 保留 GitHub 返回值。它们支持来源核对，本地静态检查只核对记录间一致性，不重新请求上游。
