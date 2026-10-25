# 科研记录模板

将三个 JSON 示例复制到自己的研究项目中，分别命名为 passport.json、claims.json、audits.json。登记实际材料后替换示例 ID、相对路径、工作流 SHA 与所有 SHA-256。示例的零摘要、文字和 unknown 均为占位内容，不能作为成功证据。

- [研究状态清单](passport.example.json)
- [主张证据账本](claims.example.json)
- [审查账本](audits.example.json)
- [完整字段与过期规则](../../workflows/academic-state.md)

所有材料路径均相对于明确指定的研究根目录。不要把私人论文、未公开数据和审查记录提交到这个公开路由仓库。

```sh
python -m router academic-check /path/to/study/passport.json \
  --research-root /path/to/study --research-id my-study \
  --snapshot-sha FULL_WORKFLOW_SOURCE_SHA
```

追加 `--submission` 检查已登记主张的投稿前置记录。退出码 0 表示该次机械检查通过，2 表示过期或门槛未满足，1 表示契约或读取错误。输出始终保留 `scientific_truth: not-verified`。

SHA-256 按实际文件原始字节计算。先登记研究材料与主张账本，再形成审查和对应输入绑定，最后更新清单中的审查账本摘要。账本和审查内容一旦修改，需要重新计算相关摘要并保留旧版记录。
