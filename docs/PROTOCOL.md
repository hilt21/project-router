# 加载与证据协议

## 任务与版本

新任务先读取 main 的 `channels/stable.json`。核对 repository、schema_version、version 和完整 40 位 commit_sha。再按 commit_sha 读取配置和对应路由。后续文件全部固定到该 SHA，禁止混用 main。

main 的 release record 与稳定指针必须一致。源提交可以早于 release record。继续同一任务时使用原 SHA；明确新任务或用户要求升级时重新解析指针。上下文压缩后用回执恢复版本和完成状态，必要时重读源文件。

GitHub 连接器应使用精确 repository、path 和 ref。只拿到搜索摘要、截断内容或错误响应时，文件尚未加载完成。缺少 GitHub 工具时报告能力缺口，不能声称已加载远程规则。

## 依赖与完整性

读取路由声明的 rules、workflow 和 skills。使用 registry/skills.yaml 找到技能路径，再核对 skills.lock.json。锁文件为每个 skill 包中的文件记录 SHA-256。CLI 校验覆盖增删及内容修改，校验失败不自动重新锁定。

纯连接器可按同一协议执行，不需要运行 Python。无法计算内容摘要时，在回执中保留未验证项；源 SHA 与成功文件读取仍需记录。

反馈 skill 只在出现实质反馈时加载，它不属于每次执行包的必需技能。反馈指引、回执模板和本协议同样从固定源 SHA 读取。

## 状态与授权

| 状态 | 含义 |
| --- | --- |
| ready | 指令和声明能力满足，工作尚未执行 |
| needs-input | 渠道尚未确定或需要拆分，独立只读工作可继续 |
| blocked | 关键能力缺失，依赖操作暂停 |
| complete | 回执中的验收项均有通过证据 |
| partial / failed | 仅部分完成，或已经失败 |
| unknown / not-run | 未取得足够证据，或未执行 |

Python 输出 `mutations_authorized: false` 表示它从不授予写权限；当前用户的实际授权仍由宿主判断。声明工具可用也不代表连接、额度、目标权限或外部动作成功。

## 回执

紧凑回执用于普通复杂任务，包含项目、SHA、已读技能、实际验证、未验证项。机器回执参见 [示例](../templates/receipt.example.json)。示例含虚构 SHA，不能当作真实运行证据。

`receipt-check` 只验证结构和部分一致性，无法证明证据真实性。模型自述不得作为 passed 的唯一依据。所有实质失败及阻塞都记录；成功记录可以采样，统计时保留采样口径，不能只挑成功样本。

发布记录中的 Work 新建对话、压缩恢复和私有仓库能力保持 not-run，直到取得对应平台证据。agent 独立探针与 CLI 单测不替代这些测试。
