# 评测分层

`routing.yaml` 保留原有二十个案例，`academic-routing.yaml` 增加十八个科研案例，验证确定性项目路由、显式模式、能力缺失和错误处理。`python -m router eval` 读取所有 `*routing.yaml`，不调用模型，不证明文案质量或 skill 实际执行。

单元故障测试覆盖断链、循环、路径越界、跨项目引用、锁文件漂移、证据误报和版本回滚。

独立 agent 探针使用原始输入材料和 skill 文件，在不泄露预期答案的条件下检查实际产物。探针结果单独记录。真实 Work 端到端测试按 docs/WORK_ACCEPTANCE.md 执行。

候选版需要与旧版使用相同输入比较，并加入反例。关键约束可以选择项目独有、可观察的要求，以减少模型常识造成的归因混淆。小样本通过不代表所有表达都可靠。

科研的两项合成任务探针见 [manifest](probes/academic/manifest.json)，保留源 SHA、输入、输出摘要与逐项观察。使用新上下文的原生子任务执行，未建立跨模型独立性；主 agent 回读产物进行有边界的语义判断。没有无 skill 对照，因此不能把结果归因为 skill 的净增益。

`probes/check_artifacts.py` 验证已保存探针文件的摘要与原有内容长度约束。它不重新执行模型，不把词匹配或完整性检查记为语义正确性。探针包可在 manifest 的 clean source_sha 下按相同 project、mode 和声明能力重建，校验 packet_sha256 后使用保存的原始 input。
