# Changelog

## V6.6.0

日期：2026-07-21

### 数据安全

- 新增 Excel 安全读取、同目录临时写入、写后回读验证和原子替换。
- 已有 Excel/TXT 写入前自动备份，失败时保留或恢复原文件。
- 损坏、不可读历史文件不再被当作空表继续处理。
- 客户池、企业状态等人工维护表保留未知字段和原列顺序。
- 企业入口验证写回前检测外部修改，避免覆盖人工更新。

### 工程化

- 建立核心 Excel 数据契约和模块索引。
- 由 `paths.py` 统一登记正式、业务、调试 Excel 及 TXT 输出路径。
- 路径基于项目根目录计算，支持从其他工作目录启动。
- 建立覆盖主结果、客户池、跟进、企业状态、项目输出、调试输出和路径的离线回归体系。

### 验证

- 48 项单元测试全部通过，无失败、无错误。
- 54 个项目 Python 文件通过无字节码语法检查。
- 故障注入覆盖文件不存在、损坏、读取失败、写入失败、备份失败、临时文件失败和跨目录启动。
- 测试前后正式 Excel/TXT SHA-256 一致；未访问网络，未运行正式采集。

### 兼容性

- 不改变采集、评分、过滤、唯一 ID、合并或去重业务规则。
- 不改变既有 Excel 字段含义、列结构、文件名或默认输出位置。

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
