# Project Status

## 当前版本

PackagingRadar V6.5.5

## 当前阶段

工程化：Documentation System。

## 已完成模块

- 主招标采集与结果导出。
- 日报生成。
- 高价值线索筛选。
- 客户池构建。
- 跟进任务生成。
- 联系方式候选导入。
- 企业采购入口发现、排序、导入和验证。
- 环评、扩产、生产项目监控。
- 模拟数据安全测试。
- V6.5 路径标准化：`paths.py`。
- V6.5 第一批核心脚本路径迁移。

## 正在开发

- V6.5.5 文档体系。
- `docs/` 下项目状态、架构、数据流、模块索引、故障排查和发布检查文档。

## 下一步计划

- V6.6 新增 `utils/excel_helper.py`。
- 统一 Excel 读写、补列、去重、保存和自动备份。
- 将更多固定业务路径迁移到 `paths.py`。
- 继续降低业务状态表被多个脚本直接覆盖的风险。

## 当前数据统计

最近一次已记录验证：

- Raw：330
- Filtered：64
- High Value Leads：6
- Customer Pool：3

## 风险事项

- `main.py` 默认 `USE_SAMPLE_DATA = False`，运行会访问公开网页并写入正式结果。
- `customer_pool.xlsx` 被多个脚本写入。
- `enterprise_url_status.xlsx` 被多个企业入口脚本写入。
- 多个调试脚本会直接覆盖 debug Excel/TXT。
- Windows 环境存在 `__pycache__` 写入权限问题，验证时优先使用 `python -B`。
- Excel 文件被打开时，脚本写入可能失败。
