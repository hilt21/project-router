# 内容创作管线

将项目的 Content Creation & Publishing Instructions 整合到路由、公共规则、平台规范、执行 skill 和复盘模板中。公开仓库只保留方法和基于公开来源的评测材料，不存放私有聊天记录。

| 原有要求 | 唯一维护位置 |
| --- | --- |
| Attention、Value、Trust、Sharing、Retention；总体创作原则 | [公共内容规则](../rules/content.md) |
| 六个传播机制、证据规则、发布前六问 | [公共内容规则](../rules/content.md) |
| 平台选择、单平台与双平台作用域 | [内容路由](../routes/content-studio.md) |
| 微信受众、叙事、50～300 字、1～3 张 3:4 图与指标 | [微信规则](../rules/content-wechat.md) |
| LinkedIn 受众、叙事、100～300 词、单张 4:3 图与指标 | [LinkedIn 规则](../rules/content-linkedin.md) |
| 核验、选角度、文案、视觉、发布与阶段边界 | [工作流](../workflows/content.md)及 [skill](../skills/craft-channel-content/SKILL.md) |
| 真实数据、观察窗口、复用机制与下一轮实验 | [复盘模板](../templates/content-feedback.md) |

当前明确要求优先于平台默认值。单篇文案不默认附视觉方案；只要视觉方案时不生图；用户直接要求生图时不增加确认环节。平台选择与交付阶段是两个独立维度，CLI 的 mode 只表示平台。

使用项目短入口读取频道并锁定 SHA。与 schema 1 相比，schema 2 的命令行调用必须由宿主显式传入平台；两个平台的规范不再同时进入单平台执行包。

```sh
python -m router packet --project content-studio --mode wechat --task '已选主题，只写正文' --capability web-search
python -m router packet --project content-studio --mode dual --task '共用证据，分别创作' --capability web-search
```

图像工具声明与授权仍由宿主判断，只有本次确实要生图时才传入 `--generate-images`。Python 只编译规则，不生成内容、不执行发布。

## 设计库候选接入

[Design Library](https://github.com/hilt21/design-library) 独立维护条目。同步时从其已发布提交复制绑定 `content-studio` 的入口和依赖，使用活动技能锁校验。Work 仍按自身固定的 router SHA 读取，保留设计库来源 SHA。索引按阶段和条目 ID 查找，允许以明确别名选择。视觉方案未指定风格时用原流程。

```sh
python -m router packet --project content-studio --mode wechat --capability web-search \
  --task '为 EMB 写一篇微信贴图短文并审校，做单色封面方案，先别生图' \
  --design-entry draft-review=channel-draft-review \
  --design-entry visual-plan=单色海报
```

该候选包只在调用方显式传入阶段和条目时读取对应方法。Work 文档入口按工作流解析当前需求，选中后读取同样的文件。验收记录见 [设计库候选验收](qa/design-library.md)。

DHH 历史选题的旧版与候选版云端产物、LinkedIn 仅正文任务和验收边界见 [验收报告](qa/content-pipeline.md)。
