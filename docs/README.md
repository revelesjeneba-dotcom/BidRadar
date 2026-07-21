# PackagingRadar Documentation

PackagingRadar 是面向纸箱、包装箱、纸制品包装等行业的招标、项目线索、客户池和跟进管理工具。项目当前重点从功能扩展转入工程化标准化，目标是让路径、数据流、模块边界和发布流程可维护、可审计。

## 目录结构

- `*.py`：业务脚本、采集脚本、导入脚本、调试脚本和测试脚本。
- `paths.py`：核心业务数据文件路径登记。
- `*.xlsx`、`*.txt`：正式结果、业务数据、调试数据和日报。
- `FILE_MAP.md`：文件与数据流盘点。
- `docs/`：项目文档体系。
- `test_output/`：模拟测试输出，已从 Git 跟踪中排除。
- `backup/`：手工备份目录，已从 Git 跟踪中排除。

## 快速开始

1. 阅读 `docs/PROJECT_STATUS.md` 确认当前版本、阶段和风险。
2. 阅读 `docs/DEVELOPMENT_RULES.md` 确认开发约束。
3. 修改路径时只改 `paths.py`。
4. 新增 Excel 输出时同步更新 `FILE_MAP.md` 和 `docs/DATA_FLOW.md`。
5. 运行真实采集前确认 `main.py` 当前模式和输出目标。

## 每日工作流程

1. 查看 `git status --short`，确认工作区变化。
2. 阅读 `docs/TODO.md`，选择一个明确任务。
3. 只做一类修改，避免业务改动和重构混在一起。
4. 如涉及路径、Excel 或模块边界，同步更新文档。
5. 完成后按 `docs/RELEASE_CHECKLIST.md` 做检查。

## Git 提交规范

- 一次提交只做一类修改。
- 文档、路径迁移、业务逻辑、数据文件更新应拆开提交。
- 提交信息建议格式：`V6.5.5 建立 docs 文档体系`。
- 提交前检查是否误改 Excel、TXT 或运行输出文件。

## 版本管理

- 当前文档体系从 V6.5.5 开始维护。
- 版本变更记录写入 `docs/CHANGELOG.md`。
- 当前状态写入 `docs/PROJECT_STATUS.md`。
- 发布前使用 `docs/RELEASE_CHECKLIST.md`。
