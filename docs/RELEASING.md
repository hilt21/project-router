# 发布与回滚

源提交必须已通过静态校验、路由基准和故障测试，并推送到 GitHub。后续行为变更使用 PR，附范围、复现、评测和未验证项。合并及更新稳定入口遵循用户授权。

```sh
python -m router validate
python -m router eval
python -m unittest discover -s tests -v
git add .
git commit -m 'Describe the source change'
git push origin main
```

检查该源提交的 GitHub Actions 状态后，用完整 SHA 创建发布记录。以下 SHA 为占位说明，必须替换为实际提交：

```sh
python -m router release-create --version v0.1.0 --commit FULL_SOURCE_COMMIT_SHA
python -m router promote --version v0.1.0 --channel stable
python -m router validate
git add releases channels
git commit -m 'Publish the validated source snapshot'
git push origin main
```

release-create 拒绝已存在版本和与源提交不一致的受管文件。源快照与发布记录分两次提交，避免提交 SHA 自引用。发布记录提供已验证范围，首次版本明确为 preview。

回滚时选择已有 release，运行 promote，再提交指针变更。不得改写旧 release，不需要 force push。已有任务继续旧 SHA，新任务读取回滚后的指针。

MVP 不自动修改 ChatGPT 项目设置，不自动合并候选 PR，也不依赖定时任务运行。
