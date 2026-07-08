# Work Log

## 2026-07-08

- 完成 BidRadar 项目迁移。
- 源目录：`D:\Codex\MarbleFinder\BidRadar`
- 目标目录：`D:\AI-Workspace\01_BidRadar_招标雷达`
- 实际复制 63 个文件。
- 排除 `__pycache__`、`.git`、`.pyc`。
- 四个关键文件均存在：`main.py`、`run_bidrader.bat`、`config.py`、`requirements.txt`。
- 尚未运行采集程序。
- 下一步是检查入口、依赖和运行模式。

## 2026-07-08 静态检查

- 已阅读目标目录文件结构。
- 已检查 `main.py`、`run_bidrader.bat`、`config.py`、`requirements.txt`。
- 执行 `python -m compileall .` 时，因写入 `__pycache__` 字节码触发 Windows `PermissionError`，命令未完成。
- 使用不写入字节码的静态 `compile()` 检查 39 个 `.py` 文件，结果全部通过。
- 未运行 `main.py`。
- 未运行 `run_bidrader.bat`。
- 未访问外部网站。
- 未改写 Excel 或 TXT 数据文件。

## 2026-07-08 模拟数据运行测试

- 测试目的：验证新目录可在不访问外部网站、不运行真实采集、不覆盖正式结果的前提下完成一次模拟数据流程。
- 测试入口：`test_sample_run.py`。
- 输出目录：`test_output`。
- 运行命令：`python test_sample_run.py`。
- 测试前备份目录：`backup\2026-07-08_before_test`。
- 已备份文件：`bid_results.xlsx`、`daily_report.txt`、`raw_results_debug.xlsx`。
- 运行结果：成功。
- 模拟原始数据数量：7。
- 过滤去重后数量：5。
- 价值等级统计：`★=2`、`★★=1`、`★★★=1`、`★★★★★=1`。
- 跟进优先级统计：`最高=1`、`中=1`、`低=1`、`观察=2`。
- 生成文件：`test_output\test_bid_results.xlsx`、`test_output\test_daily_report.txt`。
- 已确认网络访问次数为 0。
- 已通过哈希对比确认正式结果文件未被覆盖。
- 兼容问题：`exporter.export_to_excel()` 会读取已有输出文件作为历史并影响重复测试的“本次新增”统计；测试入口改用独立测试导出逻辑，只写入 `test_output`。

## 2026-07-08 Git 初始化

- Git 初始化完成。
- 初始提交号：`ebeda8b`。
- 初始提交后工作区状态：干净。
- `backup/` 和 `test_output/` 已通过 `.gitignore` 排除。
- `__pycache__/`、`*.pyc`、`*.pyo` 已通过 `.gitignore` 排除。
- `test_sample_run.py` 已纳入版本管理。
