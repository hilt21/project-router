---
name: mono-color-editorial
description: Design a one-ink editorial cover from a theme or reference image, with a repeatable recipe, exact text, and a generation prompt. Use for monochrome print, halftone, risograph or explicit mono-color requests.
---

# 单色编辑海报

确认主题、受众、画幅、交付阶段、需要保留的主体特征，以及逐字文案或无字要求。沿用当前语言和渠道规则。没有参考图时标明主体是概念表达。工程细节以输入资料为依据。

## 选择配方

读取 `design-system/recipes.json`。先应用用户显式值，再按内容匹配配方。技术、研究和机械主题默认 technical-specimen。突出主体的封面选 editorial-cover。安静的个人观察选 quiet-observation。

记录配方 ID、所有覆盖值及原因。用范围内的确定值描述画面。相同输入重试时保留配方，只调整已失败的局部。明确单墨时使用一种墨色，纸色和网点疏密提供深浅。显式双色任务读取 `design-system/colors.json`，为两种墨版分别指定主体与强调作用。

## 建立视觉关系

- 选一个可识别主体。主体大小按配方范围确定，保留一个具有形状的主要留白区域。
- 让标题与主体形成配方指定的关系，如围绕标本、压住主体裁切边缘或纳入阅读节奏。每页只安排一个主要视觉事件。
- 按字体角色设置标题、辅助事实和标注。中文使用相同角色的可读字形，保留整字和合理行距。字体层级依据配方，不固定复用一种字体组合。
- 网点须表现印刷复制过程。技术主题使用清晰版面与轻度网点。做旧、粗颗粒和手写标记需符合主题，一张图最多一种手工标记语汇。
- 系列图共享纸色、墨色、间距和事实标注规则。允许各主题选择不同构图，逐张保留独立图片 ID。

## 输出与检查

交付配方和 `PROMPT.md` 实例。配方必须包含画幅、主体特征、精确文字、语言、纸色、墨色、构图、主体及留白占比、标题关系、字体角色和纹理。按 `CHECKLIST.md` 标明方案检查与实际图片检查的结果。进入生图阶段时由宿主调用既有工具和逐图流程。

默认配方不合适时读取完整 `design-system/compositions.json` 和 `design-system/typography.json`。需要判断常见错误时读取 `references/examples.md`。上游数据的来源和改动记录在条目清单，许可见 `references/UPSTREAM-LICENSE.txt`。
