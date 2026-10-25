# project-router

在一个 Git 仓库维护 ChatGPT Work 各项目的路由、工作流、规则和 skills。每个项目只保留短入口，任务开始时读取已发布快照。

提供“新项目脑暴”“内容创作”和“学术研究”三条路由，以及十一个指令型 skills。源代码和配置采用 MIT 许可证。

## 开始使用

1. 在目标 ChatGPT 项目中确保 GitHub 连接可以读取 `hilt21/project-router`。
2. 将下列入口文件的**正文**复制到对应项目的指令设置中：
   - [新项目脑暴入口](bootstrap/new-project.md)
   - [内容创作入口](bootstrap/content-studio.md)
   - [学术研究入口](bootstrap/academic-research.md)，使用 preview 频道
3. 新建该项目内的 Work 对话，发送一个真实任务。首个回执应包含实际源 SHA、已读 skills 和未验证项。

维护工作流时只修改本仓库并发布版本。入口协议本身升级时才需要更新项目设置。修改仓库不会自动更新已安装插件，也不会改变运行中任务的快照。

`channels/stable.json` 指向可复现的 MVP 预览版本。`stable` 表示固定的分发入口；当前成熟度为 `preview`，真实新建 Work 对话、上下文压缩恢复和私有仓库访问仍需按 [验收步骤](docs/WORK_ACCEPTANCE.md) 验证。详见 [QA 报告](docs/QA.md)。

学术研究候选快照通过 `channels/preview.json` 分发，阶段与证据契约见 [科研使用说明](docs/ACADEMIC.md)。七个阶段分别处理问题、文献、数理、实验、写作、评审和投稿准备，按需加载。v0.2.0-rc.2 已完成真实 Work 新对话、缺材料和跨对话回执恢复的限定检查，观察及未测范围见 [真实 Work 科研验收](docs/qa/academic-work-ui.md)。

## 系统如何工作

项目 ID 固定项目边界；路由选择工作流；规则限定行为；skill 提供具体方法；实际工具由宿主提供。Python 只编译执行包和检查配置，不执行任务、不安装 skills、不授予权限。

```mermaid
flowchart TD
  A[项目入口] --> B[读取稳定指针]
  B --> C[固定源 SHA]
  C --> D[加载必要路由和规则]
  D --> E[执行与验证]
  E --> F[结果与证据回执]
  F -->|实质偏差| G[反馈 Issue]
  G --> H[候选 PR 与回归]
  H -->|审阅通过| B
```

## 本地校验与执行包

需要 Python 3.11 以上。纯 GitHub 连接器读取无需这些依赖。

```sh
python -m pip install -e .
python -m router validate
python -m router lock --check
python -m router eval
python -m unittest discover -s tests -v
python -m router packet --project new-project --task '调研开源方案' --capability github-read --capability web-search
python -m router packet --project academic-research --mode math --task '检查当前推导' --capability github-read
```

内容路由采用 schema 2。宿主按请求及上下文显式传入 `--mode wechat`、`--mode linkedin` 或 `--mode dual`，仅加载对应平台规范。省略时进入 `select-channel`，由宿主推荐或必要时澄清；明确双渠道时直接选择 dual。CLI 不再通过内容关键词猜渠道，调用方迁移时需要传入 mode。创作阶段、证据与复盘约束见 [内容工作流](docs/CONTENT.md)。

科研阶段由宿主依据请求选择并传入 `--mode`。省略时进入 `select-stage` 盘点；`pipeline` 只在明确要求完整流程时使用。可选计算能力缺失不会阻塞推理，但相应验证保持未运行。

宿主确认本次阶段需要生图时传入 `--generate-images`，由 CLI 检查相应工具声明。该参数不授予生图权限；“先别生图”或只写视觉方案时不传入。

CLI 返回码：0 表示静态通过或执行包就绪；1 表示配置错误；2 表示能力缺失、需要补充输入或评测失败。`ready` 只说明声明依赖满足，不代表任务已执行或已获得写权限。

CLI 针对当前工作树编译候选执行包。要复现发布版，先按稳定指针的 SHA 在独立 worktree 检出源提交；输出中的 `source.kind` 应为 `git-commit`，且 `source.sha` 与指针一致。未提交工作树不能作为发布版运行证据。

## 维护文档

- [架构与边界](docs/ARCHITECTURE.md)
- [科研工作流与本地证据检查](docs/ACADEMIC.md)
- [加载协议与回执](docs/PROTOCOL.md)
- [发布及回滚](docs/RELEASING.md)
- [反馈闭环](feedback/README.md)
- [评测说明](evals/README.md)
- [参考来源及引入原则](registry/README.md)

本仓库为公开仓库。业务状态放在各自项目；反馈保留脱敏证据，不保存完整聊天或凭据。
