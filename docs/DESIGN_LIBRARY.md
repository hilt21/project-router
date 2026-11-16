# 设计方法包的调用与维护

Design Library 管理方法、配方、提示词和来源记录。本仓库管理项目绑定、执行阶段、渠道规则和回执。首批五类条目通过 registry/design-library.json 配置，加入已有项目无需修改路由代码。

| 项目 | 阶段 | 条目 | 当前交付范围 |
| --- | --- | --- | --- |
| content-studio | draft-review | channel-draft-review | 文案及改动说明 |
| content-studio | visual-plan / image-generation | mono-color-editorial | 单色配方和提示词；生图由宿主执行 |
| new-project | slide-design | technical-deck-design | 逐页设计与可编辑对象规格 |
| new-project | 3d-design | threejs-reference-rebuild | 几何、枢轴及运动约束规格 |
| new-project | web-review | web-design-review | 页面或截图证据上的问题清单 |

后三类先用于研究和方案阶段。PPT 渲染器、Three.js 构建器及浏览器运行环境继续由宿主或目标项目提供。配置可将条目绑定到其他已有项目，仍须使用条目声明的阶段并通过预算检查。

## 按需读取

```sh
python -m router packet --project content-studio --mode wechat \
  --task '审校短文并设计单色封面，停在提示词阶段' --capability web-search \
  --design-entry draft-review --design-entry visual-plan=单色海报

python -m router packet --project new-project --mode research \
  --task '规划五页技术演示稿' --capability web-search --capability github-read \
  --design-entry slide-design=PPT设计

python -m router packet --project content-studio --mode wechat \
  --task '选择单色封面的具体色板' --capability web-search \
  --design-entry visual-plan=mono-color-editorial \
  --design-resource mono-color-editorial=design-system/colors.json
```

只有配置了 default 的阶段可省略条目 ID。普通任务不加载设计条目。多阶段组合需要显式登记，validate 枚举各项目模式、单阶段及已登记组合，检查完整执行包。按需资源在实际编译时检查，超限时拆分阶段或减少当前不需要的资源，不静默截断。

index.json 只作为定位与完整性输入。执行包包含选中条目的来源 SHA、内容摘要和已选文件，不塞入全部候选清单。未选中条目增长不会增加同一任务的上下文大小。维护端仍校验完整活动快照和技能锁。

## 来源更新与恢复

从设计库干净的已发布提交运行 tools/export.py --sync-router，并传入完整来源 SHA。同步按照本仓库绑定选择条目，检查当前文件没有漂移，在 staging 中构建完整快照，最后原子切换活动指针。维护命令限 POSIX 系统，用进程文件锁串行同步。故障保证覆盖进程异常和写入失败，不宣称断电落盘持久性。

重复同步同一来源是幂等操作。指针切换失败后可重试。切换成功前旧快照有效。当前任务始终读取固定 router 提交，与维护工作区的切换隔离。回滚时从先前设计库来源重新同步，再更新锁并验收。旧快照可由 Git 恢复，删除非活动快照前确认其已提交。

源码漂移会阻止同步，不自动覆盖消费端手动改动。审核后将有用改动回迁到设计库，再重新同步。上游更新比较使用设计库的 tools.check_upstream，只输出命中文件及受影响用例，不自动采纳上游提交。

## 回执与证据

设计回执沿用 plan 的 design_library 对象，包含来源 SHA、条目 ID、阶段、content_sha256 和 documents。source_readback 只记录实际读取文件。status 为 complete 时，所有选中文档必须有匹配的读取摘要，并提供 artifacts 数组，每项含相对路径和 sha256。

```sh
python -m router --root /path/to/pinned-clean-router receipt-check /path/to/receipt.json \
  --artifact-root /path/to/outputs
```

核对需要对应的干净 router 提交。工具检查来源、读取摘要与实际产物字节；不会据此证明输出事实或视觉质量。partial 回执允许缺少尚未读取文件，但已有摘要必须匹配。语义质量、实际工具执行、人工检查与新建 Work 对话分别记录。

[候选验收记录](qa/design-library.md) 包含自动回归和实际代理产物的证据范围。
