# 加载与证据协议

## 任务与版本

新任务先读取 main 的 `channels/<channel>.json`。频道来自本项目入口，未指定时为 stable，不静默切换。核对 repository、schema_version、version 和完整 40 位 commit_sha。再按 commit_sha 读取配置和对应路由。后续文件全部固定到该 SHA，禁止混用 main。

main 的 release record 与稳定指针必须一致。源提交可以早于 release record。继续同一任务时使用原 SHA；明确新任务或用户要求升级时重新解析指针。上下文压缩后用回执恢复版本和完成状态，必要时重读源文件。

GitHub 连接器应使用精确 repository、path 和 ref。只拿到搜索摘要、截断内容或错误响应时，文件尚未加载完成。缺少 GitHub 工具时报告能力缺口，不能声称已加载远程规则。

## 依赖与完整性

读取路由声明的 rules、workflow 和 skills。使用 registry/skills.yaml 找到技能路径，再核对 skills.lock.json。锁文件为每个 skill 包中的文件记录 SHA-256。CLI 校验覆盖增删及内容修改，校验失败不自动重新锁定。

纯连接器可按同一协议执行，不需要运行 Python。无法计算内容摘要时，在回执中保留未验证项；源 SHA 与成功文件读取仍需记录。

反馈采用每条用户消息的**意图检查点**：先依据上下文判定明确纠错、长期约束、可观察故障或已验证经验，再按需要加载反馈 skill。一次性编辑、引用文字及未验证推测不自动成为长期规则。反馈 skill 不属于每次执行包的必需技能，命中后从同一固定 SHA 读取 `skills/capture-router-feedback/SKILL.md` 和 `feedback/README.md`，保留实际已读证据；不能记作初始执行包已加载。反馈检查不依赖关键词自动分类器，具体判断与去重规则见 `feedback/README.md`。

## 按模式加载

路由 schema 1 保留现有单流程和渠道辅助选择行为。schema 2 使用 `default_mode`、`needs_input_modes` 和 `mode_config`；每个声明的 mode 必须有一个配置项，即使其内容为空。

先读取路由正文并确定 mode，再读取公共依赖与该 mode 的依赖。`mode_config` 只允许 `includes`、`rules`、`skills`、`required_capabilities`、`optional_capabilities`。公共依赖始终生效；所选模式追加依赖，禁止用模式配置移除公共约束。

schema 2 的 CLI 只使用显式 `--mode` 或声明的默认模式，不通过关键词猜测科研阶段。宿主根据本次明确请求和当前材料选择模式；意图不明时进入声明的盘点模式。有明确阶段但缺材料时，保留该阶段并报告材料缺口。

CLI 校验所有模式的依赖图和完整执行包字节预算。编译时仅输出当前模式的文档、技能和工具要求，包含传递依赖。可选能力缺失只影响相应验证，不自动阻塞独立工作，也不能据此声称验证已经运行。必需能力缺失优先标为 blocked。

阶段切换时，在原源 SHA 下重新选择模式与加载依赖。上一阶段未读的 skill 不能提前登记为已读。数据材料不会因被 skill 引用而获得规则权限。

## 状态与授权

| 状态 | 含义 |
| --- | --- |
| ready | 指令和声明能力满足，工作尚未执行 |
| needs-input | 阶段、渠道或必要输入尚未确定，独立只读工作可继续 |
| blocked | 关键能力缺失，依赖操作暂停 |
| complete | 回执中的验收项均有通过证据 |
| partial / failed | 仅部分完成，或已经失败 |
| unknown / not-run | 未取得足够证据，或未执行 |

Python 输出 `mutations_authorized: false` 表示它从不授予写权限；当前用户的实际授权仍由宿主判断。声明工具可用也不代表连接、额度、目标权限或外部动作成功。

## 回执

紧凑回执用于普通复杂任务，包含项目、SHA、已读技能、实际验证、未验证项。机器回执参见 [示例](../templates/receipt.example.json)。示例含虚构 SHA，不能当作真实运行证据。

`receipt-check` 只验证结构和部分一致性，无法证明证据真实性。模型自述不得作为 passed 的唯一依据。所有实质失败及阻塞都记录；成功记录可以采样，统计时保留采样口径，不能只挑成功样本。

出现实质反馈时，用户可见回执区分 `drafted`、`linked-existing`、`filed`、`blocked`，以工具回读确认外部写入；这些状态不改变任务本身的 complete/partial 语义。Memory 提示不作为仓库写入证据。

发布记录中的 Work 新建对话、压缩恢复和私有仓库能力保持 not-run，直到取得对应平台证据.agent 独立探针与 CLI 单测不替代这些测试。
