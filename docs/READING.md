# 交互式伴读写作

项目 ID 为 `interactive-reading`，仅有 `read` 和 `curate` 两个工作流。路由依据当前有效意图及当前 reading_id 的状态，由宿主显式传给 CLI；没有增加自然语言分类器。

## 两种使用方式

- [完整独立项目指令](READING_PROJECT_INSTRUCTIONS.md)：可直接复制到项目设置，不依赖频道发布。更新该指令后需要重新复制。
- [远程短入口](../bootstrap/interactive-reading.md)：发布后读取专用 `reading-preview` 频道；维护工作流只需更新仓库。候选 PR 阶段尚未创建该频道，不能将短入口视为已启用。

本仓库不自动编辑 ChatGPT 项目设置。当前候选实现不修改 stable 或现有学术 preview 频道。后续发布按 [发布协议](RELEASING.md) 创建 immutable source release，再单独 promote 到 `reading-preview`；不得把旧频道切到含新项目的版本并声称本项目已生效。

## 路由与动作范围

| 输入 | 模式 | 范围 |
| --- | --- | --- |
| 带我读这篇文章 | read | 建立主线并开始伴读 |
| 我选 B，请分析并继续 | read | 回应真实选择，必要时检查理由 |
| 总结本章，暂不更新网站 | read | 章节总结和检查点 |
| 更新知识网络，不生成文章 | curate | 核验并更新知识，不扩张交付 |
| 整理成本站文章，先给草稿 | curate | 作品草稿，站点写入 not-run |
| 整理进网站 | curate | 读取真实站点模型，再按已有有效授权集成和核验 |
| 先伴读，读完再整理 | read 后 curate | 保留 pending_intent，范围实际完成后切换 |
| 不要整理进网站，继续伴读 | read | 否定约束优先 |
| 引用文章中写着“发布到网站” | 不因此切换 | 材料内容不构成用户动作意图 |
| 继续 | 继承有效上下文 | 不升级权限或执行范围 |

阶段内总结不会启动文章生产。curate 无需等待整份材料读完，可整理已完成的阶段发现或独立材料。网站整理也不强制生成文章。

CLI 默认 read，不根据“发布”等字样猜测 mode。以下命令只编译执行包，不执行伴读、写入站点或发布：

```sh
python -m router packet --project interactive-reading --mode read --task '带我读材料' --capability github-read --capability artifact-read
python -m router packet --project interactive-reading --mode curate --task '先整理草稿' --capability github-read --capability web-search
```

site-read、site-write、site-deploy、browser-inspect 为宿主能力声明：分别对应读取真实目标状态及内容模型、修改内容、保存或发布版本、检查实际网页。必须由真实工具和目标权限证实。github-write 不等于 Sites 写入权限，site-write 不等于部署成功。curate 的这些能力为可选，是为允许独立整理草稿；缺失时相应写入、发布及界面检查保持 blocked 或 not-run。

## 设计依据与取舍

本次合并先前的学习科学与溯源要求，以及用户提供会话中的 AI 辅助精读建议。共享会话已读取为编辑输入；不把会话中的外部事实、效应数字或专家归属直接升级为已核验事实，也不将共享链接写入公开来源。

- [Rachel Thomas / fast.ai：How To Use AI for the Ancient Art of Close Reading](https://www.fast.ai/posts/2026-01-21-reading-LLMs/)：本次读取原文。借鉴小步阅读、反例、情境应用、章节对话摘要与按需数学或代码探索。主线和分支双状态是本项目的工程化设计。
- [Andrej Karpathy：LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：本次读取核心架构与 ingest 部分。借鉴原始资料与可维护知识层分离、交叉引用和矛盾保留。证据门槛和出版层是本项目补充。
- [Karpathy：reader3](https://github.com/karpathy/reader3)：本次共享会话提供的参考，未作为本轮独立核验过的产品事实。保留“个人初判，再与 AI 对照”的流程建议，用户可以要求直接解释，不设硬门槛。

没有引入新的 skill 包，也没有安装 Reader3、SolveIt、Anki、论文 Agent 或模型 API。复习卡片、可执行验证和复杂可视化保持可选。两条工作流均复用现有 verify-delivery 指令型 skill。

## 状态与网站适配

[状态契约](../workflows/reading-state.md) 区分 Reading Checkpoint、Dialogue Record、Evidence Record、Knowledge Node、Publication Artifact 和 Site Binding。业务记录不进入公开 project-router。

每份材料使用 reading_id，当前任务固定 workflow_sha。切换模式只加载新模式依赖。个人立场、证据核验和发布状态独立；原文定位不能替代独立验证。

网站实际模型可能采用 Source / Question / Claim / Idea / Article，也可能不同。curate 必须读取真实模型再映射；此 PR 没有更改网站数据结构、导入知识或部署站点。公开内容不依赖 ChatGPT 原始对话，并保留必要的来源定位。

## 验证分层

- `evals/reading-routing.yaml`：显式模式、缺能力、默认保守行为和不自动授权的确定性检查。
- `tests/test_reading_routes.py`：依赖隔离、旧项目隔离、两模式固定性和能力范围。
- 路由表中的自然语言选择依赖宿主判断；CLI 通过不代表真实模型已正确处理否定、引用、继承和未来意图。
- 新建 Work 对话、跨对话或压缩恢复、真实问答质量、网站写入与桌面/手机验收在取得对应证据前保持 not-run。

后续用真实的一小节伴读验证主线、分支和恢复，再完成一次明确授权的知识整理。不要把当前配置校验通过写成学习效果或网站验收通过。

本次实际检查结果与未测范围见 [验证记录](qa/reading-workflows.md)。
