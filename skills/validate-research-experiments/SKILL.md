---
name: validate-research-experiments
description: Design or validate engineering simulations, experiments, statistical analyses, and reproducibility evidence. Use for baselines, ablations, sensitivity, uncertainty, convergence, runtime constraints, or rerun checks.
---

# 验证实验与仿真

先读取同快照的[科研契约](../../workflows/academic-state.md)。明确本次工作是设计、执行、结果分析或复现；已有授权覆盖的步骤直接推进。

1. 将每个核心主张映射到实验、基线、指标和失败判据。按需要加入对照、消融、极限工况、参数敏感性、噪声和故障条件。
2. 检查数据来源、划分、泄漏、测量误差及模型假设。针对工程系统检查物理约束、动态响应、数值步长或网格收敛与实时计算条件。
3. 执行前核对实际计算工具、输入和资源。仅在用户授权的任务范围内运行；不能把计划、生成的脚本或环境检查记为已经做过实验。保留失败运行与负面结果。
4. 记录数据版本、代码提交、环境、参数、随机种子、重复次数、命令、日志和图表重建方法。受限数据说明访问范围，不擅自公开。
5. 检查效应大小、估计精度、不确定度及适用统计假设。按研究需要处理多重比较、混杂和因果识别；p 值单独不足以证明工程价值。
6. 独立复运行后才登记复现成功。确定性和随机实验分别定义与问题尺度相符的比较准则，不使用通用百分比容差。无法复运行时明确只有分析证据。

交付实验计划或实际验证报告，包含逐主张证据、异常、未运行项、可复现条件与局限。区分仿真、台架和现场证据；计划结果和合成演示数据不能写入真实 Results。
