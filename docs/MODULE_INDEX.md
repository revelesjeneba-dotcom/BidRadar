# Module Index

| 模块名 | 功能 | 输入 | 输出 | 是否联网 | 是否写 Excel | 优先级 |
|---|---|---|---|---|---|---|
| `browser_runner.py` | Playwright 浏览器封装 | 环境浏览器路径 | 无 | 是 | 否 | A |
| `candidate_contact_importer.py` | 联系方式候选导入客户池 | `customer_contact_candidates.xlsx`、`customer_pool.xlsx` | `customer_pool.xlsx` | 否 | 是 | A |
| `candidate_importer.py` | 企业入口候选导入状态表 | `enterprise_candidates.xlsx`、`enterprise_url_status.xlsx` | `enterprise_url_status.xlsx` | 否 | 是 | B |
| `candidate_ranker.py` | 企业入口候选评分 | `enterprise_candidates.xlsx`、`enterprise_sources.py` | `enterprise_candidates.xlsx` | 否 | 是 | B |
| `commercial_sources.py` | 商业来源配置 | 无 | 无 | 否 | 否 | C |
| `config.py` | 主流程配置 | 无 | 无 | 否 | 否 | A |
| `contact_finder.py` | 搜索联系方式候选 | `customer_pool.xlsx` | `customer_contact_candidates.xlsx` | 是 | 是 | B |
| `crawler.py` | 公开招标采集 | `sources.py` | 内存记录 | 是 | 否 | A |
| `customer_pool.py` | 构建客户池 | `high_value_leads.xlsx`、`target_companies.xlsx`、`customer_pool.xlsx` | `customer_pool.xlsx` | 否 | 是 | A |
| `debug_raw_results.py` | 招标 raw 调试导出 | `sources.py` | `raw_results_debug.xlsx` | 是 | 是 | C |
| `eia_debug.py` | 环评诊断 | `eia_raw_results.xlsx` 或联网 raw | `eia_raw_debug.xlsx`、`eia_diagnosis.txt` | 条件是 | 是 | C |
| `eia_keywords.py` | 环评关键词 | 无 | 无 | 否 | 否 | B |
| `eia_monitor.py` | 环评项目监控 | `eia_sources.py`、`eia_projects.xlsx` | `eia_projects.xlsx` | 是 | 是 | B |
| `eia_sources.py` | 环评来源配置 | 无 | 无 | 否 | 否 | B |
| `enterprise_crawler.py` | 企业采购页采集 | `enterprise_sources.py` | 内存记录 | 是 | 否 | B |
| `enterprise_source_manager.py` | 企业入口状态表生成 | `enterprise_sources.py`、`enterprise_url_status.xlsx` | `enterprise_url_status.xlsx` | 否 | 是 | B |
| `enterprise_sources.py` | 企业来源配置 | 无 | 无 | 否 | 否 | B |
| `enterprise_validator.py` | 企业入口验证 | `enterprise_url_status.xlsx` | `enterprise_url_status.xlsx` | 是 | 是 | B |
| `expansion_keywords.py` | 扩产关键词 | 无 | 无 | 否 | 否 | B |
| `expansion_monitor.py` | 扩产项目监控 | `expansion_sources.py`、`expansion_projects.xlsx` | `expansion_projects.xlsx` | 是 | 是 | B |
| `expansion_sources.py` | 扩产来源配置 | 无 | 无 | 否 | 否 | B |
| `exporter.py` | 主结果导出 | 记录列表、历史 Excel | 主结果 Excel | 否 | 是 | A |
| `followup_manager.py` | 跟进任务生成 | `customer_pool.xlsx` | `customer_pool.xlsx`、`followup_tasks.xlsx` | 否 | 是 | A |
| `high_value_filter.py` | 高价值线索筛选 | `bid_results.xlsx` | `high_value_leads.xlsx` | 否 | 是 | A |
| `industry_filter.py` | 行业过滤 | `config.py` | 无 | 否 | 否 | A |
| `jianyu_importer.py` | 剑鱼 raw 导入 | `raw_jianyu_results.xlsx`、`bid_results.xlsx` | `bid_results.xlsx` | 否 | 是 | B |
| `jianyu_search.py` | 剑鱼搜索采集 | `keywords.py` | `raw_jianyu_results.xlsx` | 是 | 是 | B |
| `keywords.py` | 剑鱼关键词 | 无 | 无 | 否 | 否 | B |
| `main.py` | 主流程入口 | `config.py`、`sources.py` 或 `sample_data.py` | `bid_results.xlsx`、`daily_report.txt` | 默认是 | 是 | A |
| `manual_import.py` | 手工导入 | `manual_import.xlsx`、`bid_results.xlsx` | `manual_import.xlsx`、`bid_results.xlsx` | 否 | 是 | B |
| `paths.py` | 路径登记 | 无 | 无 | 否 | 否 | A |
| `project_keywords.py` | 生产项目关键词 | 无 | 无 | 否 | 否 | B |
| `project_monitor.py` | 生产项目监控 | `project_sources.py`、`production_projects.xlsx` | `production_projects.xlsx`、`production_raw_debug.xlsx` | 是 | 是 | B |
| `project_sources.py` | 生产项目来源配置 | 无 | 无 | 否 | 否 | B |
| `reporter.py` | 日报生成 | Excel 结果 | `daily_report.txt` | 否 | 否，写 TXT | A |
| `sample_data.py` | 模拟数据 | 无 | 内存记录 | 否 | 否 | A |
| `scoring.py` | 招标评分 | 记录字典 | 评分字典 | 否 | 否 | A |
| `source_discovery.py` | 企业入口发现 | `enterprise_sources.py`、`enterprise_candidates.xlsx` | `enterprise_candidates.xlsx` | 是 | 是 | B |
| `sources.py` | 招标来源配置 | 无 | 无 | 否 | 否 | A |
| `target_company_manager.py` | 目标企业表维护 | `target_companies.xlsx` | `target_companies.xlsx` | 否 | 是 | B |
| `test_sample_run.py` | 模拟安全测试 | `sample_data.py` | `test_output/*` | 否，主动阻断 | 是 | A |
| `tests/test_excel_contracts.py` | 核心 Excel 列契约检查 | 现有核心 Excel、源码列定义 | 无 | 否 | 否 | A |
| `tests/test_business_baseline.py` | 模拟数据业务回归基线 | `sample_data.py`、纯业务函数 | 无 | 否，主动阻断 | 否 | A |
