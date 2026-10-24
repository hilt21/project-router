# MVP QA

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
| GitHub CI | pending | 推送后记录实际运行链接 |
| Work 当前会话连接器回读 | pending | 发布后按固定 SHA 回读 |

上述探针为独立 agent 本地读取，未注入父会话结论。探针输出摘录和可测篇幅检查已保存；小样本不能证明普遍稳定性。

首轮曾出现 content-brief-only 失败：否定生图请求被关键词误判。改为显式动作参数后通过。真实反馈已记录在 [Issue 1](https://github.com/hilt21/project-router/issues/1)，保留了反例。

当前尚未完成真实新建 Work 项目对话、长对话压缩和私有仓库测试。验收步骤见 [WORK_ACCEPTANCE.md](WORK_ACCEPTANCE.md)。
