# Skills 引入原则

当前有十一个自定义指令型 skills，许可证为 MIT，来源为本仓库，未安装到宿主技能目录。skills.lock.json 对全部包文件进行摘要校验。科研工作流的设计参考和固定来源见 [academic-references.yaml](academic-references.yaml)。

外部技能须审阅：来源与完整 commit SHA、逐文件许可证、脚本与网络依赖、可用工具、作用域及真实 Work 试验。未验证候选不进入活动注册表。高 stars 不能替代这些检查。

设计参考：

- [Agent Skills 标准](https://agentskills.io/specification)：目录和渐进加载。
- [Rulesync](https://github.com/dyoshikawa/rulesync)：统一来源与选择性引入。
- [Microsoft APM](https://github.com/microsoft/apm)：声明依赖与版本锁定。
- [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin)：规则包和有证据的经验回写。
- [ChatGPT Web Skills](https://github.com/0xheycat/chatgpt-web-skills)：项目路由与检查点的边界说明。
- [OpenAI Plugins](https://github.com/openai/plugins)：当前插件分发样例。openai/skills 已标记弃用。

本仓库没有复制这些项目的实现代码或打包其技能。当前活动注册表没有第三方代码依赖，Python 工具仅依赖 PyYAML。

科研 skills 为本仓库独立编写。ARS-Codex 标注 CC BY-NC 4.0，本仓库登记其固定提交及所参考机制。活动技能继续使用 source: local、activation: document；外部脚本、hooks、模型 API 和整套 ARS 包均未引入。
