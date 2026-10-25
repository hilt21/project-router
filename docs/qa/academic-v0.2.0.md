# 学术研究候选版 QA

日期：2026-10-25，Asia/Shanghai。范围为科研路由、七个文档式 skills、研究记录契约和只读检查器。

## 静态与确定性证据

- 原有二十个路由案例保持通过，新增十八个科研路由案例通过。
- 七个科研 skill 经 skill-creator quick_validate 检查；原有四个 skill 的锁定内容保持一致。
- 九种科研模式逐一编译，执行包约 17–21 KB，低于 40 KB 预算，包含元数据。单阶段只加载当前领域 skill；pipeline 首次只加载公共指令。
- 单元与集成测试覆盖模式隔离、传递工具依赖、未选阶段断链、执行包预算、来源支持与存在性区分、摘要过期、研究 ID、工作流 SHA、失败与未知记录保留、主张撤回及只读行为。
- 本次检查器通过只表示本地契约和登记关系满足。scientific_truth 为 not-verified，投稿门槛最多为 eligible-for-human-review。

命令：`python -m router validate`、`python -m router lock --check`、`python -m router eval`、`python -m unittest discover -s tests -v`、`python evals/probes/check_artifacts.py`。最终提交的实际结果与数量见 [验证记录](academic-verification.json)。

## 独立上下文任务探针

探针执行包由本地提交 `606d6e54430e92491f47ddba2ae18ba89686834d` 生成，其文件树与 [公开等价提交](https://github.com/hilt21/project-router/commit/abe49d97a86fd96c67296d4ee5f0325539613f2e) 完全相同，树 SHA 为 `23ed40a637a6660dd64f9967860637c0530a5065`。[执行清单](../../evals/probes/academic/manifest.json) 保存映射、完整执行包、原始输入和输出摘要。后续变更集中于记录检查器和契约；七个领域 skill 的内容未修改。

| 探针 | 观察到的交付行为 | 证据 |
| --- | --- | --- |
| 数理审查 | 找出半正定与严格凸混用，给出全部最优解，区分存在与唯一，拒绝将三点采样当证明 | [输入](../../evals/probes/academic/math.input.md)、[输出](../../evals/probes/academic/math.output.md) |
| 写作证据约束 | 由均值计算10%，去除30%、现场验证、未运行扰动和因果断言，保留合成与不确定度缺口 | [输入](../../evals/probes/academic/write.input.md)、[输出](../../evals/probes/academic/write.output.md) |

两项由新上下文的原生子任务执行，主 agent 读取完整产物后登记观察。模型独立性未建立；没有无 skill 对照，不能估计 skill 净增益，不能用两个合成样例推断真实论文的检出率或误报率。

## 待验证范围

真实 Work 新建对话、上下文压缩、私有仓库、真实跨研究隔离、真实论文效果和领域专家复核均为 not-run。没有调用专业相似性检测、外部模型服务或实际投稿。验收操作见 [Work 验收](../WORK_ACCEPTANCE.md)。

候选版使用 preview 频道；发布记录保留成熟度和各项证据状态。GitHub Actions、静态检查与入口回读不替代真实平台或论文质量验证。
