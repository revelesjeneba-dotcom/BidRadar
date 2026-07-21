# BidRadar V6.6.0 招标雷达

## 项目目标

BidRadar 面向纸箱、包装箱和纸制品包装业务，将公开招标、生产项目、环评、扩产及企业采购入口等线索整理为可跟进的结构化数据。系统负责采集、行业过滤、地区识别、价值评分、结果归档、客户池维护和跟进任务生成。

## 当前架构

- 采集层：`crawler.py`、企业入口脚本及项目监控脚本负责获取公开信息。
- 业务层：`industry_filter.py`、`scoring.py`、客户池、跟进和候选导入模块保持既有规则。
- 数据层：`paths.py` 统一登记项目根目录下的 Excel/TXT 路径；`utils/excel_helper.py` 提供安全 Excel 读写。
- 输出层：主结果、项目结果、客户池、状态表、调试 Excel 和 UTF-8 文本报告。
- 验证层：`tests/` 提供离线回归、数据契约、安全写入、故障注入和跨工作目录路径测试。

详细结构见 `docs/ARCHITECTURE.md`、`docs/DATA_FLOW.md` 和 `FILE_MAP.md`。

## V6.6.0 数据安全能力

- Excel 读取失败立即报错，禁止把损坏或不可读历史当作空表覆盖。
- 已有 Excel/TXT 写入前自动备份到 `backup/auto/`。
- 使用同目录临时文件、写后回读验证和原子替换；失败时保留原文件。
- 客户池及状态表保留未知人工字段和原列顺序。
- 企业入口验证写回前检查外部修改，避免覆盖人工更新。
- `paths.py` 使用项目根目录绝对 `Path`，不依赖启动时的当前工作目录。
- Excel 数据契约、模块索引和 48 项离线回归测试覆盖主要安全场景。

## 环境与使用方式

推荐使用项目虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

安全的离线验证命令：

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

主入口为 `main.py`，Windows 批处理入口为 `run_bidrader.bat`。当前 `main.py` 的 `USE_SAMPLE_DATA = False`，正式运行会访问公开网页并可能更新正式 Excel/TXT；运行前必须确认联网授权、数据备份和文件未被 Excel 占用。发布验证不得以 `main.py` 正式模式代替离线测试。

## 主要输出

- 主结果：`bid_results.xlsx`、`daily_report.txt`
- 客户与跟进：`customer_pool.xlsx`、`followup_tasks.xlsx`、`customer_contact_candidates.xlsx`
- 企业入口：`enterprise_candidates.xlsx`、`enterprise_url_status.xlsx`
- 项目线索：`production_projects.xlsx`、`eia_projects.xlsx`、`expansion_projects.xlsx`
- 派生数据：`target_companies.xlsx`、`high_value_leads.xlsx`
- 调试数据：`raw_results_debug.xlsx`、`raw_jianyu_results.xlsx`、`eia_raw_debug.xlsx`、`production_raw_debug.xlsx`、`eia_diagnosis.txt`

所有正式路径以 `paths.py` 为准；字段契约见 `docs/EXCEL_CONTRACTS.md`。

## 运行边界

- 未确认前不要运行 `main.py`、真实采集、浏览器自动化或 URL 验证脚本。
- 不直接编辑或删除 `backup/auto/` 中用于恢复的最新备份。
- 数据文件与代码/文档应分开检查和提交，提交前确认无 `*.xlsx`、`*.txt`、临时文件、备份、`.pyc` 或 `__pycache__` 进入版本变更。
