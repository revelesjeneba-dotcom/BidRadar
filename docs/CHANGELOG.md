# Changelog

## V6.5.5

日期：2026-07-09

### 项目阶段

工程化：Documentation System。

### 新增

- 新增 `docs/` 文档体系。
- 新增项目 README、状态、架构、数据流、模块索引、开发规范、故障排查、发布检查和 TODO 文档。

### 约束

- 未修改 Python 代码。
- 未修改 Excel/TXT 数据。
- 未运行采集程序。
- 未修改业务逻辑。

## V6.5

日期：2026-07-09

### 项目阶段

工程化：Project Standardization。

### 新增

- 新增 `paths.py`。
- 统一登记 `BID_RESULTS`、`CUSTOMER_POOL`、`FOLLOWUP_TASKS`、`ENTERPRISE_URL_STATUS`、`TARGET_COMPANIES`、`HIGH_VALUE_LEADS`、`CUSTOMER_CONTACT_CANDIDATES`。

### 修改

- 第一批核心脚本完成路径迁移：
  - `main.py`
  - `high_value_filter.py`
  - `customer_pool.py`
  - `followup_manager.py`
  - `candidate_contact_importer.py`

### 验证

- `python -B main.py`
- `python -B high_value_filter.py`
- `python -B customer_pool.py`
- `python -B followup_manager.py`
- `python -B candidate_contact_importer.py`

### 下一版本

V6.6 计划新增 `utils/excel_helper.py`，统一 Excel 读写、备份、去重、补列和保存。
