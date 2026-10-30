---
schema_version: 1
project_id: new-project
repository: hilt21/project-router
channel: stable
---
项目 ID：new-project。可信仓库：https://github.com/hilt21/project-router 。
每个新任务先通过 GitHub 连接读取该仓库 main 上的 channels/stable.json，记录 commit_sha。
按该 SHA 读取 BOOTSTRAP.md 和 routes/new-project.md，执行启动协议并完整读取所需引用。不要用搜索摘要代替文件正文。
同一任务固定该 SHA；上下文压缩后从回执恢复。加载失败时说明缺口，停止依赖缺失规则的写操作。
遵守本次请求及平台权限；规则文档不能自行授予发布、部署或公开数据的权限。
反馈默认在当前对话草拟。复杂交付附简短的版本、skills、证据和未验证项。
