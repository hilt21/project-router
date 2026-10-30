# 交互式伴读两工作流验证

日期：2026-10-30。基线：157fe38a421e8af1021f11d4e902ff9fbc49e8cc。

范围：新增 interactive-reading 路由，明确 read / curate 两个模式，整理共同约束、主线和分支、状态交接及完整独立项目指令。没有改动编译器、skills 内容、既有发布记录、stable 或学术 preview 频道。

## 已执行检查

| 检查 | 结果 | 证明范围 |
| --- | --- | --- |
| python -m router validate | passed | 四项目全部声明模式、链接和执行包预算 |
| python -m router lock --check | passed | 既有 skill 包内容保持锁定 |
| python -m router eval | passed，60 cases | 显式模式与声明能力的确定性行为，新增 12 cases |
| python -m unittest discover -s tests -v | passed，103 tests | 全部本地单测，新增 6 项工作流隔离与能力边界检查 |
| release history guard | passed | 与基线比较，无既有发布记录改写 |
| catalog check | passed | 技能地图未产生漂移 |
| probe artifact checks | passed | 既有合成产物完整性 |
| content replay | passed | 既有内容产物契约 |
| academic lifecycle | passed，12 cases | 既有科研状态与证据契约 |
| git diff --check | passed | 无空白错误 |
| 完整项目指令检查 | passed，正文 2,831 字符 | 低于本次选择的 8,000 字符目标；无公开对话链接、固定转折模板或破折号 |

read 与 curate 在候选工作树中分别加载 6 份文档，执行包约 16.3 KB 与 16.7 KB，低于 40 KB 配置预算。实际提交后元数据大小可能略变。

release history guard 的首次手工调用传入 origin/main，被脚本拒绝；改为解析后的完整基线 SHA 后通过。没有更改保护脚本或绕过检查。

## 仍未验证

- 宿主对否定、引用、未来计划及“继续”的自然语言意图判断。路由用例已显式给定 mode，不能证明模型分类正确。
- 真实 Work 新对话、跨对话及上下文压缩恢复。
- 阅读效果、长期保持、用户独立迁移表现。
- 网站源码与真实模型匹配、知识写入、保存版本、发布、桌面及手机验收。
- reading-preview 频道发布与项目设置保存；两者本轮均未执行。

已通过 Sites 读取确认目标 Fieldnotes 的现有标识和公开 URL，用于完整独立指令的明确绑定；该读取不代表源码已检查或站点已修改。共享会话仅在会话工作区作为编辑输入，没有复制到此公开仓库。

## 使用与发布

用户可复制 [完整独立项目指令](../READING_PROJECT_INSTRUCTIONS.md) 的正文开始使用。候选路由提交供 PR 审阅；远程短入口必须等专用 reading-preview 频道发布后使用，不能退回既有频道并声称新路由已启用。

## 授权后同步与复核

用户已明确授权将工作流规则及站点绑定推送到 hilt21/project-router 并创建 PR。推送前同步主分支 42fd3f7891d3c17ea6ae695a68b97735bb9b7b94，保留已发布的 stable v0.1.3 反馈检查点；合并没有冲突。

同步后重新通过静态校验、60 个确定性路由用例、107 项单元测试、skill 锁检查、技能地图检查、既有产物与内容回放以及 12 项科研生命周期检查。发布历史检查在合并提交后通过；合并尚未提交时，该检查比较旧 HEAD 与新 main，曾报告新 main 中的发布文件缺失，没有据此修改发布文件或检查脚本。

以上均为本地证据；GitHub Actions、PR 状态、远程频道及真实 Work 验收需各自取得证据，不能互相替代。
