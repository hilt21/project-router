---
name: threejs-reference-rebuild
description: Plan and verify a procedural Three.js reconstruction using reference images and confirmed geometry or kinematics.
---

# 参考图到 Three.js 程序化模型

1. 标注可见轮廓、对称关系、比例、零件和遮挡。分别记录图中可见、资料确认、需要测量或用户确认的特征。
2. 先确定坐标系、单位、主轴、分件、父子层级、枢轴和自由度，再建模。对机械机构明确输入、约束、输出、极限位置和已知尺寸。图片无法证实的内部结构在建模规格中标为未知。
3. 用参数化几何表达主要零件。保存基准姿态和参数。外观与运动的控制变量分离，运动和读数使用同一状态。
4. 从正视、侧视和斜视复核外形。对基准位、行程中间位和极限位检查枢轴、轨迹、干涉与回零。外观相似和运动学正确分别记录验收结果。
