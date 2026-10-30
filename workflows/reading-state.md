---
id: reading-state
project_id: interactive-reading
includes: []
---

# 两工作流的最小状态与交接

业务记录保留在对应阅读项目或目标知识站点，规则仓库只维护通用指令和合成样例。以下为逻辑字段；以真实站点契约为准，不强制引入数据库或改造其 schema。

| 对象 | 最小记录 |
| --- | --- |
| Reading Checkpoint | project_id、reading_id、workflow_sha、mode、材料 ID 与版本、实际 read_scope、主线位置与 next_step、开放分支和返回点、pending_intent、缺失项 |
| Dialogue Record | dialogue_id、题干、选项、真实回答与理由、反馈、原记录或编辑重述标识、缺失范围、关联知识 ID |
| Evidence Record | source_id、具体主张、原文定位、支持的范围、访问范围、证据状态、冲突、公开可访问的来源或真实来源说明 |
| Knowledge Node | note_id、revision、内容与类型、归属、证据引用、适用条件、个人立场、关系、公开范围 |
| Publication Artifact | article_id、revision、读者问题、内容组件、note_id 与 revision 引用、来源定位、编辑状态、实际发布状态 |
| Site Binding | 已确认的目标站点 ID 或仓库、公开 URL、真实模型版本或摘要、内容版本、实际授权范围；未知项保持 unknown |

原作者陈述、证据核验、个人立场、编辑状态和发布状态分别记录。`source-located` 只表示定位到表述；`cross-checked` 记录独立检查的具体范围；`disputed`、`unverified` 和 `withdrawn` 可保留，不强行压成二元真假。

`pending_intent` 记录未来动作、约定触发范围及原始授权，不以时间经过或模型自述判断完成。`next_step` 说明当前待做动作；“继续”只能继续它，不能扩大范围。完成 curate 后保留 read 的主线位置。

新材料可分配新 reading_id；对同一材料的续读与修订保持原 ID。相同材料的不同研究问题可拆分 session，但应显式建立关联。跨对话恢复必须核对 reading_id、原 workflow_sha 和实际材料版本。

私密过程记录与公开导出使用不同视图。导出前移除私密问答、内部路径和不可公开附件；保留公开理解所需的摘编内容与证据说明。知识和作品公开链接指向站内条目及可访问原始来源。
