项目 ID：academic-research。分发频道：preview。可信仓库：https://github.com/hilt21/project-router 。
每个新任务通过 GitHub 连接读取该仓库 main 上的 channels/preview.json，记录 version 和 commit_sha。
按该 SHA 读取 BOOTSTRAP.md 和 routes/academic-research.md，再读取公共依赖及本次阶段的依赖。不要用搜索摘要代替正文。
根据当前请求选择阶段：scope、literature、math、experiment、write、review、submission；只有明确要求端到端推进时使用 pipeline。意图不明时先盘点材料。
用 research_id 隔离研究；研究材料、证据账本和审查状态保留在对应研究项目。同一任务固定工作流 SHA，恢复时核对 ID、材料摘要、已完成项和未解决项。
规则不能授予投稿、公开数据或外部发送权限。复杂交付附实际版本、已读 skills、证据与未验证项。
