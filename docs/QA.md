# MVP QA

科研扩展候选版的独立范围、证据和待验证项见 [academic-v0.2.0.md](qa/academic-v0.2.0.md)。下文保留 v0.1.0 的验收记录。

日期：2026-10-24（北京时间）。版本：v0.1.0 预览。

| 层 | 结果 | 证据与范围 |
| --- | --- | --- |
| 静态图与 skill 完整性 | passed | 两条路由、四个 skills；断链、循环、作用域和锁文件检查 |
| 路由基准 | 20/20 passed | evals/routing.yaml；仅验证确定性编排 |
| 单元及故障测试 | 30/30 passed | 路径、漂移、证据误报、源版本和指针回滚 |
| Skill Creator 校验 | 4/4 passed | 本地 quick_validate.py 校验四个技能包 |
| 独立调研探针 | passed，范围有限 | evals/probes/research.json；基于虚构冻结快照 |
| 独立内容探针 | passed，范围有限 | evals/probes/content.json；中文 194 字，英文 166 词；只给定素材 |
| 包安装与 CLI | passed | 本地 editable 安装、packet 和 receipt-check 已运行 |
| GitHub CI | passed | Python 3.11 和 3.12 两个任务均通过，[源提交运行记录](https://github.com/hilt21/project-router/actions/runs/40107216692) |
| Work 当前会话连接器回读 | 17/17 一致 | 用完整源 SHA 读取启动协议、两条路由及其规则、工作流和 skills，与本地已测试文件逐字一致 |
| 发布后入口链路 | passed | main 上的两个入口和 stable 指针读取成功，再按解析出的 SHA 重读启动协议和两条路由；缺失路径返回预期错误 |

上述探针为独立 agent 本地读取，未注入父会话结论。探针输出摘录和可测篇幅检查已保存；小样本不能证明普遍稳定性。

首轮曾出现 content-brief-only 失败：否定生图请求被关键词误判。改为显式动作参数后通过。真实反馈已记录在 [Issue 1](https://github.com/hilt21/project-router/issues/1)，保留了反例。

源提交：`6ef26eb04e1219c6aa9b73d662eb2f0e9512460d`。远端文件树与本地测试文件树相同，树 SHA 为 `9cdbbe252d3bc193038e2c5e6c74785b3600cda5`。连接器回读明细见 [github-readback.json](qa/github-readback.json)。

发布 PR [2](https://github.com/hilt21/project-router/pull/2) 已通过 CI 并合并，[合并后 CI](https://github.com/hilt21/project-router/actions/runs/40107731096) 也通过。完整入口链路证据见 [stable-chain.json](qa/stable-chain.json)。已从独立 detached worktree 重建两条执行包，源 SHA 均与指针一致。

源提交中的初始 QA 文档保留推送前状态；本报告属于交付证据，按 main 上的最新版本读取。额外自动代码审查仍在运行，未计入已通过证据。

当前尚未完成真实新建 Work 项目对话、长对话压缩和私有仓库测试。验收步骤见 [WORK_ACCEPTANCE.md](WORK_ACCEPTANCE.md)。
