---
name: audit-mathematical-rigor
description: Audit mathematical models, proofs, optimization arguments, and engineering derivations. Use to check assumptions, units, feasibility, optimality, uniqueness, stability, boundary cases, or numerical counterexamples.
---

# 审查数理严谨性

先读取同快照的[科研契约](../../workflows/academic-state.md)。接收模型、推导、变量、假设和拟支持的主张。缺少推导时保留缺口，继续当前数理阶段。

1. 列出变量、参数、单位、定义域、约束、符号约定及物理含义。区分显式假设、推导所需条件与尚未证明的命题。
2. 从定义、定律或已核实的定理逐步检查关键推导，标明每一步依据。检查定理条件、除零、换极限或积分顺序等操作的合法性。
3. 按实际主张检查可行性、存在性、唯一性、最优性、稳定性或收敛性。区分充分条件与必要条件；半正定、严格凸、强凸不能混用。KKT 的必要性和充分性分别检查。
4. 检查退化参数、容量或权重为零、边界解、饱和、噪声和离散实现。主动构造反例，优先攻击支撑核心结论的最弱步骤。
5. 有计算工具时，按需独立符号复算、数值对照或反例搜索，记录代码、输入、环境和实际输出。没有工具时明确计算未运行。有限数值样本不能替代一般证明。
6. 将每项结论标为严格证明、符号工具结果、数值证据、经验假设或未解决。单一模型换审查角色不能形成独立证据。

交付变量与假设表、推导依赖、逐项问题及定位、反例或复算记录、对核心主张的影响和修复顺序。关键公式或证明条件未解决时，阻断相应数学主张的通过状态；保留可以独立完成的工作。
