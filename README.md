# BidRadar 招标雷达

## 项目用途

BidRadar 是一个面向纸箱、包装箱、纸制品包装等行业关键词的招标和项目线索整理工具。项目会从公开信息源或本地样例数据中收集线索，过滤行业相关内容，识别地区，评分，并导出 Excel 结果和日报文本。

## 当前主要功能

- 公开招标信息采集、行业关键词过滤、地区识别和价值评分。
- 招标结果导出到 `bid_results.xlsx`，并生成 `daily_report.txt`。
- 环评、扩产、生产项目等项目线索监控模块。
- 高价值线索筛选、客户池维护、跟进任务生成。
- 企业采购入口发现、候选网址排序、状态维护和验证。
- 手工导入、剑鱼网原始结果导入、调试数据导出等辅助流程。

## 主要入口文件

- `main.py`：主入口。根据 `USE_SAMPLE_DATA` 决定使用本地模拟数据或调用 `crawler.py` 采集公开网页，然后构建结果、导出 Excel、生成日报。
- `run_bidrader.bat`：Windows 批处理入口。切换到脚本所在目录后执行 `python main.py`。

## 主要模块

- `config.py`：项目名称、行业关键词、采购关键词、重点省份、地区别名、输出文件和 Excel 字段配置。
- `crawler.py`：公开招标来源采集。
- `exporter.py`：结果去重、唯一 ID、Excel 导出。
- `reporter.py`：日报文本生成。
- `sample_data.py`：本地模拟数据。
- `scoring.py`：线索价值评分、等级、优先级和推荐动作。
- `industry_filter.py`：纸箱/包装行业相关性判断。
- `project_monitor.py`、`eia_monitor.py`、`expansion_monitor.py`：生产、环评、扩产项目监控。
- `high_value_filter.py`：高价值线索筛选。
- `customer_pool.py`、`followup_manager.py`、`contact_finder.py`、`candidate_contact_importer.py`：客户池、跟进任务和联系方式处理。
- `enterprise_crawler.py`、`enterprise_validator.py`、`enterprise_source_manager.py`、`source_discovery.py`、`candidate_importer.py`、`candidate_ranker.py`：企业采购入口发现、导入、排序和验证。
- `manual_import.py`、`jianyu_search.py`、`jianyu_importer.py`、`debug_raw_results.py`、`eia_debug.py`：手工导入、剑鱼数据、调试和诊断辅助模块。

## 主要数据文件

- `bid_results.xlsx`：主招标结果。
- `daily_report.txt`：主日报。
- `raw_results_debug.xlsx`、`raw_jianyu_results.xlsx`：原始/调试结果。
- `eia_projects.xlsx`、`eia_raw_debug.xlsx`、`eia_diagnosis.txt`：环评项目结果和诊断。
- `production_projects.xlsx`、`production_raw_debug.xlsx`：生产项目结果和调试数据。
- `expansion_projects.xlsx`：扩产项目结果。
- `high_value_leads.xlsx`：高价值线索。
- `customer_pool.xlsx`、`followup_tasks.xlsx`、`customer_contact_candidates.xlsx`：客户池、跟进任务、联系方式候选。
- `enterprise_candidates.xlsx`、`enterprise_url_status.xlsx` 及其备份文件：企业采购入口候选和验证状态。
- `target_companies.xlsx`、`manual_import.xlsx`：目标企业和手工导入模板/数据。

## 当前运行方式

- 批处理方式：双击或执行 `run_bidrader.bat`，实际会运行 `python main.py`。
- 命令行方式：在项目目录执行 `python main.py`。
- 当前 `main.py` 中 `USE_SAMPLE_DATA = False`，表示默认走公开网页采集路径；若要做新目录安全测试，建议先人工确认是否临时切换为模拟数据。

## 安全规则

- 不要在未确认运行模式前运行 `main.py` 或 `run_bidrader.bat`。
- 不要在未确认前运行任何真实采集、浏览器自动化或外部网站访问程序。
- 不要直接改写已有 Excel、TXT 数据文件，除非已经备份并明确知道对应模块的写入目标。
- 不要初始化 Git，直到项目结构、运行模式和数据文件归档规则确认完成。
- 对依赖安装、Playwright 浏览器安装、真实采集测试应单独记录命令和结果。

## 尚待确认的问题

- 新目录首次运行测试是否先将 `USE_SAMPLE_DATA` 调整为 `True`。
- 现有 Excel 数据文件哪些是正式数据，哪些是调试、备份或可再生成文件。
- 是否需要固定 Python 版本和创建独立虚拟环境。
- Playwright 浏览器依赖是否已安装，是否允许后续进行浏览器自动化测试。
- 各采集源的访问频率、合法合规边界和失败重试策略是否需要统一配置。
- 是否需要将输出目录与源码目录分离，避免运行时覆盖迁移来的历史数据。
