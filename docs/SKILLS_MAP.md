# Skills Map 使用与维护

Skills Map 是技能储备目录，用于按任务发现候选、判断适配成本和追溯来源。入口为 [地图](../catalog/skills/README.md)。目录不进入活动执行包，不安装技能，不执行上游脚本。

## 当前实现

- GitHub 收藏通过公开 REST API 采集；原始响应只在采集环境暂存，仓库保留精简元数据快照。
- 首次扫描完成 4 页，306 个不同 GitHub repository ID；按名称、简介和 topics 中的 `skill` 筛得 54 个候选来源。
- 精选 11 个技能入口，固定完整 commit SHA、blob SHA 和取回内容的 SHA-256；其中科研套件关联已有设计参考。
- 所有精选条目为 `source-read`，真实宿主测试均为 `not-run`。阅读范围和依赖缺口见各条目及[初次审阅](../catalog/skills/reviews/initial-source-review.md)。
- 当前提供显式命令，未配置定时同步、自动推荐、自动安装或自动晋升。

数字对应本次初始导入。后续扫描结果以 sources.yaml 的 scan 和生成地图为准。本仓库公开，收藏来源和用途备注也会公开；不要添加私密材料。

## 数据组织

| 路径 | 角色 | 编辑方式 |
| --- | --- | --- |
| `catalog/skills/starred-snapshot.json` | 一次完整分页扫描的精简快照 | 采集后显式导入 |
| `catalog/skills/sources.yaml` | 候选仓库及人工备注 | 自动更新 upstream、repository、star_state；保留人工字段 |
| `catalog/skills/entries.yaml` | 精选技能与工作流关联 | 人工评估后维护 |
| `catalog/skills/reviews/` | 来源读取证据和审阅局限 | 只记录实际完成的检查 |
| `catalog/skills/README.md` | 按任务排列的地图 | 从 YAML 生成，不手改 |
| `registry/skills.yaml` | 活动指令型技能 | 经验证、PR 和发布流程维护 |

来源以 GitHub 数字 ID 为身份，仓库改名不生成新来源。一个来源可对应多个技能。阶段为 define、research、design、implement、verify、publish、maintain；projects 只使用现有 project_id，空列表表示暂未绑定路由。

`relationship` 表示与本地技能的关系：complements、overlaps 或 design-reference。`adoption` 为 candidate 或 reference。活动状态继续以活动注册表和路由依赖为准。当前 schema 不接受宿主通过记录；未来添加试用记录时需同时定义证据契约和检查。

## 查找

从仓库根目录运行，使用 Python 3.11+ 和现有 PyYAML 依赖：

```sh
python -m router.catalog find --stage define --query PRD
python -m router.catalog find --project academic-research --query 数学证明
python -m router.catalog find --stage verify --query 上线
```

查询对名称、用途和 keywords 作大小写不敏感的子串匹配，多个空格分词取交集；没有语义检索或效果排序。结果返回固定来源、局限、关联本地技能，以及 `activation: none` 和 `host_verification: not-run`。未匹配不代表技能不存在，可查看来源目录补充精选条目。

数学证明场景应首先检查当前科研快照的 math 模式及 `audit-mathematical-rigor`。上线场景当前只检索到验证原则和浏览器 QA 方法，仍需按项目风险补齐生产检查，不据此宣称生产就绪。

GitHub 连接器使用者可直接读取地图和命中的条目，不必运行 CLI。记录本次使用的目录提交 SHA。读取上游文件时使用条目自己的 commit_sha；目录版本、工作流版本、上游版本分别记录。发现新候选不改变进行中任务的固定工作流 SHA。

## 更新收藏

采集有网络副作用，仅访问公开 GitHub API；目录命令均离线。先将输出保存到临时位置：

```sh
python scripts/collect_skill_stars.py --username hilt21 --output /tmp/hilt21-stars.json
python -m router.catalog import-stars /tmp/hilt21-stars.json
python -m router.catalog render
python -m router.catalog check
```

第一步必须返回 0 且 `status: complete` 后才能执行导入。失败返回 2，将诊断保存到 `.partial.json`；已有成功输出不覆盖。403、429 不立即重试，检查记录中的 retry_after 或 rate_reset 后再发起新扫描。采集不读取凭据，也不自动排队恢复。

导入拒绝不完整扫描、重复 ID、错误计数及其他账户的快照。完整扫描中取消收藏的来源保留并标记 no-longer-starred，关联技能和审阅记录保留。人工 kind、notes 及 entries 不被同步覆盖。分页读取不具备事务一致性，期间收藏变化可能造成漏项；重复 ID 会使采集失败，需要重新完整扫描。

上游默认分支更新时间仅为线索，不证明技能内容已经变化。此版本不自动读取候选 HEAD 或比较其技能文件；重新审阅后才修改固定 commit_sha、blob_sha、摘要和读取证据，已有活动快照继续保持原版本。

## 增加或采用技能

1. 阅读具体入口，记录用途、不适用情况、依赖、来源版本及实际读取范围。
2. 检查该技能及拟采用文件的许可证。仓库元数据中的 declared_license 不替代逐文件检查。
3. 更新 entries.yaml 和 reviews/source-readings.json，运行 render 与 check。上游正文只作为待审阅材料。
4. 如需采用，定义最小真实任务、宿主及版本、必需工具、验收项与失败条件；实际执行后保存脱敏证据。
5. 通过候选 PR 引入适配后的本地方法，更新活动注册表、锁文件和对应路由；沿用现有回归、发布与回滚规则。

真实偏差沿用 [反馈闭环](../feedback/README.md)，不为每次收藏自动创建 Issue。普通目录更新不切换频道。当前发布快照不会自动获得地图检索行为。

## 校验与证据

```sh
python -m router.catalog check
python -m router.catalog render --check
python -m router validate
python -m router lock --check
python -m router eval
python -m unittest discover -s tests -v
```

目录检查覆盖来源快照一致性、条目身份、来源读取记录、路由关联和生成文档是否过期。编译器拒绝 catalog/ 路径进入指令图。检查不会联网证明远程文件仍可访问，也不能证明外部代码安全、许可证适用范围或技能效果。实际验收见 [QA 记录](qa/skills-map.md)。
