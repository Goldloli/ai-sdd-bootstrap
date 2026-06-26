# Contributing to AI SDD Bootstrap

感谢你对 AI SDD Bootstrap 的兴趣！

## 如何贡献

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feat/your-feature`
3. 提交改动：`git commit -am 'feat: add xxx'`
4. 推送分支：`git push origin feat/your-feature`
5. 提交 Pull Request

## 开发环境

本项目仅依赖 Python 标准库，无需额外安装依赖。

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

## 提交信息规范

请使用以下前缀：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 重构
- `chore:` 其他杂项

## 新增技术栈

如果你想新增一种技术栈的 harness 支持，需要：

1. 在 `scripts/ai_sdd_bootstrap.py` 的 `all_stacks()` 中加入新栈
2. 在 `scripts/ai_sdd_bootstrap.py` 中实现 `add_harness_<stack>()`
3. 在 `scripts/templates/` 中添加对应的 harness 模板
4. 更新 `SKILL.md` 和 `README.md`
5. 添加测试

## 行为准则

保持友善、尊重不同的 AI 编程工作流偏好。
