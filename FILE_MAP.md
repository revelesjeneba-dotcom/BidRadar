# BidRadar 文件与数据流盘点

盘点日期：2026-07-09

本文件基于静态阅读全部 Python 文件、README、WORK_LOG 和当前文件列表整理。未运行 `main.py`、`run_bidrader.bat` 或任何联网采集脚本。

## V6.5 路径标准化登记

新增 `paths.py` 作为核心业务数据文件路径的唯一登记入口。后续脚本改造时，应从 `paths.py` 获取以下文件路径，避免在各业务脚本中继续分散硬编码文件名。

| 路径常量 | 当前文件 | 当前用途 | 主要相关脚本 |
|---|---|---|---|
| `BID_RESULTS_FILE` | `bid_results.xlsx` | 主招标结果 | `main.py`、`exporter.py`、`high_value_filter.py`、`manual_import.py`、`jianyu_importer.py`、`reporter.py` |
| `CUSTOMER_POOL_FILE` | `customer_pool.xlsx` | 客户池 | `customer_pool.py`、`followup_manager.py`、`contact_finder.py`、`candidate_contact_importer.py` |
| `FOLLOWUP_TASKS_FILE` | `followup_tasks.xlsx` | 跟进任务 | `followup_manager.py` |
| `ENTERPRISE_URL_STATUS_FILE` | `enterprise_url_status.xlsx` | 企业采购入口状态表 | `enterprise_source_manager.py`、`candidate_importer.py`、`enterprise_validator.py` |
| `TARGET_COMPANIES_FILE` | `target_companies.xlsx` | 目标企业清单 | `target_company_manager.py`、`customer_pool.py` |
| `HIGH_VALUE_LEADS_FILE` | `high_value_leads.xlsx` | 高价值线索 | `high_value_filter.py`、`customer_pool.py` |

`paths.py` 当前只登记路径，不改变现有脚本的业务逻辑；后续迁移目标是这些脚本不再直接写死上述文件名。

## 1. 文件功能分类

### 主流程与配置

- `main.py`：主入口；按 `USE_SAMPLE_DATA` 在模拟数据和公开网页采集之间切换，构建招标结果，调用导出和日报。
- `config.py`：主流程配置；行业关键词、采购关键词、目标省份、地区别名、输出文件名和 Excel 字段。
- `paths.py`：PackagingRadar V6.5 路径登记；统一管理核心业务 Excel 文件路径。
- `exporter.py`：主招标结果去重、唯一 ID、历史合并、Excel 导出。
- `reporter.py`：读取主结果 Excel 并生成 TXT 日报。
- `scoring.py`：招标线索价值评分、星级、优先级和推荐文案。
- `industry_filter.py`：纸箱/包装行业相关性过滤。
- `sample_data.py`：本地模拟招标数据。
- `keywords.py`：剑鱼搜索关键词配置。

### 招标采集

- `crawler.py`：公开招标网页采集。
- `sources.py`：公开招标采集源和搜索 URL 配置。
- `browser_runner.py`：Playwright 浏览器启动封装，供浏览器自动化采集使用。

### 环评/扩产/生产项目监控

- `project_monitor.py`：生产项目监控，输出正式项目结果和 raw debug。
- `project_sources.py`：生产项目搜索源配置。
- `project_keywords.py`：生产项目关键词、重点行业和地区。
- `eia_monitor.py`：环评项目监控。
- `eia_sources.py`：环评项目搜索源配置。
- `eia_keywords.py`：环评项目关键词、必备关键词、生产关键词和地区。
- `expansion_monitor.py`：扩产/投产/投资项目监控。
- `expansion_sources.py`：扩产项目来源配置。
- `expansion_keywords.py`：扩产事件和重点行业关键词。

### 企业采购入口

- `enterprise_sources.py`：目标企业官网、采购入口、优先级和关键词配置。
- `enterprise_crawler.py`：企业采购平台公开页面采集。
- `enterprise_source_manager.py`：生成或更新企业采购入口状态表。
- `source_discovery.py`：通过公开搜索发现企业采购入口候选。
- `candidate_ranker.py`：对候选采购入口打分并写回候选表。
- `candidate_importer.py`：把人工确认的候选入口导入状态表。
- `enterprise_validator.py`：访问并验证采购入口是否公开、是否需要登录、是否可采集。

### 客户池与跟进

- `high_value_filter.py`：从主招标结果筛选高价值线索。
- `customer_pool.py`：用高价值线索和目标企业表构建客户池。
- `target_company_manager.py`：生成或更新目标企业清单。
- `followup_manager.py`：根据客户池生成跟进任务，并补齐客户池跟进字段。

### 联系方式收集

- `contact_finder.py`：通过公开搜索查找客户官网、电话、邮箱、采购平台候选。
- `candidate_contact_importer.py`：把人工确认的联系方式候选导入客户池。

### 手工导入与剑鱼数据

- `manual_import.py`：创建手工导入模板，并将手工整理的招标导入主结果。
- `commercial_sources.py`：商业来源配置，目前是剑鱼标讯元数据。
- `jianyu_search.py`：使用 Playwright 访问剑鱼网页并导出原始结果。
- `jianyu_importer.py`：读取剑鱼原始结果，过滤纸箱相关内容后并入主结果。

### 调试与诊断

- `debug_raw_results.py`：运行公开招标采集并导出原始调试结果。
- `eia_debug.py`：环评 raw 数据诊断，生成 debug Excel 和诊断 TXT；缺少 raw 文件时会临时联网抓取。

### 测试

- `test_sample_run.py`：模拟数据安全运行测试；安装 socket 网络拦截，只写入 `test_output`。

### Excel/TXT 数据文件

- 正式结果：`bid_results.xlsx`、`daily_report.txt`、`eia_projects.xlsx`、`production_projects.xlsx`、`expansion_projects.xlsx`
- 业务数据：`high_value_leads.xlsx`、`customer_pool.xlsx`、`followup_tasks.xlsx`、`customer_contact_candidates.xlsx`、`target_companies.xlsx`、`enterprise_candidates.xlsx`、`enterprise_url_status.xlsx`
- 调试结果：`raw_results_debug.xlsx`、`raw_jianyu_results.xlsx`、`eia_raw_debug.xlsx`、`eia_diagnosis.txt`、`production_raw_debug.xlsx`
- 备份/历史状态：`enterprise_url_status.backup.xlsx`、`enterprise_url_status.before_blank_unconfirmed.xlsx`、`enterprise_url_status.before_no_guess_cleanup.xlsx`、`enterprise_url_status.before_official_update.xlsx`
- 手工模板/数据：`manual_import.xlsx`
- 测试数据：`test_output/test_bid_results.xlsx`、`test_output/test_daily_report.txt`，当前被 `.gitignore` 排除。

## 2. Python 文件逐项说明

| 文件 | 主要职责 | 访问网络 | 读取文件 | 写入文件 | 被其他模块调用 | 建议 |
|---|---|---:|---|---|---|---|
| `browser_runner.py` | 启动 Playwright Chromium，提供浏览器页面上下文 | 是，供浏览器访问网页 | 无；读取环境变量浏览器路径 | 无 | `jianyu_search.py` | 保留 |
| `candidate_contact_importer.py` | 将确认后的联系方式候选导入客户池 | 否 | `customer_contact_candidates.xlsx`、`customer_pool.xlsx` | `customer_pool.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `candidate_importer.py` | 将确认后的企业采购入口候选导入状态表 | 否 | `enterprise_candidates.xlsx`、`enterprise_url_status.xlsx` | `enterprise_url_status.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `candidate_ranker.py` | 对企业采购入口候选 URL 打分 | 否 | `enterprise_candidates.xlsx`、`enterprise_sources.py` | `enterprise_candidates.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `commercial_sources.py` | 商业数据源配置，目前仅剑鱼 | 否 | 无 | 无 | 未发现引用 | 待确认，可能是预留配置 |
| `config.py` | 主招标流程配置 | 否 | 无 | 无 | `main.py`、`exporter.py`、`industry_filter.py`、`high_value_filter.py`、`manual_import.py`、`jianyu_importer.py`、`test_sample_run.py` | 保留 |
| `contact_finder.py` | 通过 Bing 搜索客户联系方式候选 | 是，`requests` 访问 Bing | `customer_pool.xlsx` | `customer_contact_candidates.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `crawler.py` | 公开招标网页采集 | 是，`requests` 访问 `sources.py` URL | `sources.py` | 无 | `main.py`、`debug_raw_results.py` | 保留 |
| `customer_pool.py` | 从高价值线索和目标企业表构建客户池 | 否 | `high_value_leads.xlsx`、`target_companies.xlsx`、`customer_pool.xlsx` | `customer_pool.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `debug_raw_results.py` | 导出公开招标 raw 采集诊断结果 | 是，通过 `crawler.crawl_all_sources()` | `sources.py` | `raw_results_debug.xlsx` | 暂未被其他模块导入，脚本入口 | 保留，标记为调试脚本 |
| `eia_debug.py` | 环评 raw 数据诊断和关键词统计 | 条件访问；缺少 `eia_raw_results.xlsx` 时调用 `eia_monitor` 联网 | `eia_raw_results.xlsx`、`eia_sources.py` | `eia_raw_debug.xlsx`、`eia_diagnosis.txt` | 暂未被其他模块导入，脚本入口 | 待确认，存在未纳入当前数据文件的 `eia_raw_results.xlsx` 输入 |
| `eia_keywords.py` | 环评关键词配置 | 否 | 无 | 无 | `eia_monitor.py` | 保留 |
| `eia_monitor.py` | 环评项目搜索、过滤、评分、合并导出 | 是，`requests` 访问 Bing 或公开页面 | `eia_sources.py`、`eia_projects.xlsx` | `eia_projects.xlsx` | `eia_debug.py` 会调用部分函数 | 保留 |
| `eia_sources.py` | 环评搜索源配置 | 否 | 无 | 无 | `eia_monitor.py`、`eia_debug.py` | 保留 |
| `enterprise_crawler.py` | 企业采购平台公开页采集，输出内存记录 | 是，`requests` 访问采购入口 | `enterprise_sources.py` | 无 | 未发现主流程引用，脚本入口 | 待确认，可能尚未接入主流程 |
| `enterprise_source_manager.py` | 从企业配置生成/更新采购入口状态表 | 否 | `enterprise_sources.py`、`enterprise_url_status.xlsx` | `enterprise_url_status.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `enterprise_sources.py` | 目标企业官网、采购入口和优先级配置 | 否 | 无 | 无 | 多个企业入口模块 | 保留 |
| `enterprise_validator.py` | 验证企业采购入口访问状态和可采集性 | 是，`requests` 访问状态表中的 URL | `enterprise_url_status.xlsx` | `enterprise_url_status.xlsx` | 暂未被其他模块导入，脚本入口 | 保留，运行前需备份 |
| `expansion_keywords.py` | 扩产项目关键词配置 | 否 | 无 | 无 | `expansion_monitor.py` | 保留 |
| `expansion_monitor.py` | 扩产项目采集、过滤、合并导出 | 是，`requests` 访问公开项目/公告页 | `expansion_sources.py`、`expansion_projects.xlsx` | `expansion_projects.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `expansion_sources.py` | 扩产项目来源配置 | 否 | 无 | 无 | `expansion_monitor.py` | 保留 |
| `exporter.py` | 主招标结果历史合并和 Excel 导出 | 否 | 传入的输出 Excel，如 `bid_results.xlsx` | 传入的输出 Excel，如 `bid_results.xlsx` | `main.py`、`manual_import.py`、`jianyu_importer.py`、`test_sample_run.py` | 保留 |
| `followup_manager.py` | 生成跟进任务，并补齐客户池跟进字段 | 否 | `customer_pool.xlsx` | `customer_pool.xlsx`、`followup_tasks.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `high_value_filter.py` | 从主结果筛选高价值线索 | 否 | `bid_results.xlsx` | `high_value_leads.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `industry_filter.py` | 判断文本是否命中纸箱/包装关键词 | 否 | `config.py` | 无 | `main.py`、`jianyu_importer.py`、`test_sample_run.py` | 保留 |
| `jianyu_importer.py` | 将剑鱼 raw 结果过滤后导入主结果 | 否 | `raw_jianyu_results.xlsx`、`bid_results.xlsx` | `bid_results.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `jianyu_search.py` | Playwright 访问剑鱼并导出 raw 搜索结果 | 是，浏览器访问剑鱼 | `keywords.py` | `raw_jianyu_results.xlsx` | 暂未被其他模块导入，脚本入口 | 保留，需人工确认联网和浏览器依赖 |
| `keywords.py` | 剑鱼搜索关键词 | 否 | 无 | 无 | `jianyu_search.py` | 保留 |
| `main.py` | 主招标流程入口 | 默认是，`USE_SAMPLE_DATA = False` 时调用 `crawler.py` | `config.py`、`sources.py`；导出阶段读取 `bid_results.xlsx` | `bid_results.xlsx`、`daily_report.txt` | 脚本入口 | 保留，运行前必须确认模式 |
| `manual_import.py` | 创建手工导入模板并导入主结果 | 否 | `manual_import.xlsx`、`bid_results.xlsx` | `manual_import.xlsx`、`bid_results.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `paths.py` | PackagingRadar V6.5 核心业务数据文件路径登记 | 否 | 无 | 无 | 后续供业务脚本统一引用；当前尚未接入 | 保留 |
| `project_keywords.py` | 生产项目关键词配置 | 否 | 无 | 无 | `project_monitor.py` | 保留 |
| `project_monitor.py` | 生产项目搜索、过滤、评分、合并导出 | 是，`requests` 访问 Bing 或公开页面 | `project_sources.py`、`production_projects.xlsx` | `production_projects.xlsx`、`production_raw_debug.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `project_sources.py` | 生产项目搜索源配置 | 否 | 无 | 无 | `project_monitor.py` | 保留 |
| `reporter.py` | 从 Excel 生成日报 TXT | 否 | 传入 Excel，通常 `bid_results.xlsx` 或测试 Excel | `daily_report.txt` 或传入 report 文件 | `main.py`、`test_sample_run.py` | 保留 |
| `sample_data.py` | 本地模拟招标数据 | 否 | 无 | 无 | `main.py`、`test_sample_run.py` | 保留 |
| `scoring.py` | 招标线索评分 | 否 | 无 | 无 | `main.py`、`manual_import.py`、`jianyu_importer.py`、`test_sample_run.py` | 保留 |
| `source_discovery.py` | 通过 Bing 搜索企业采购入口候选 | 是，`requests` 访问 Bing | `enterprise_sources.py`、`enterprise_candidates.xlsx` | `enterprise_candidates.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `sources.py` | 主招标公开来源配置 | 否 | 无 | 无 | `crawler.py` | 保留 |
| `target_company_manager.py` | 创建/更新目标企业清单 | 否 | `target_companies.xlsx` | `target_companies.xlsx` | 暂未被其他模块导入，脚本入口 | 保留 |
| `test_sample_run.py` | 安全模拟测试，拦截网络并写入测试目录 | 否，且主动阻断 socket | `sample_data.py`、`config.py` | `test_output/test_bid_results.xlsx`、`test_output/test_daily_report.txt` | 测试入口 | 保留 |

## 3. 输出文件汇总与覆盖风险

| 输出文件 | 生成脚本 | 类型 | 覆盖风险 |
|---|---|---|---|
| `bid_results.xlsx` | `main.py`/`exporter.py`、`manual_import.py`、`jianyu_importer.py` | 正式结果 | 中高；会读取历史合并后写回同名文件，读失败时可能以空历史重建 |
| `daily_report.txt` | `reporter.py`，由 `main.py` 调用 | 正式结果 | 高；`open(..., "w")` 每次直接覆盖 |
| `raw_results_debug.xlsx` | `debug_raw_results.py` | 调试结果 | 高；每次直接覆盖 |
| `raw_jianyu_results.xlsx` | `jianyu_search.py` | 调试/原始采集结果 | 高；每次直接覆盖，不合并历史 |
| `eia_projects.xlsx` | `eia_monitor.py` | 正式项目结果 | 中高；读取历史合并后写回，读失败时可能重建 |
| `eia_raw_debug.xlsx` | `eia_debug.py` | 调试结果 | 高；每次直接覆盖 |
| `eia_diagnosis.txt` | `eia_debug.py` | 调试诊断 | 高；`open(..., "w")` 每次直接覆盖 |
| `production_projects.xlsx` | `project_monitor.py` | 正式项目结果 | 中高；读取历史合并后写回，读失败时可能重建 |
| `production_raw_debug.xlsx` | `project_monitor.py` | 调试结果 | 高；每次直接覆盖 |
| `expansion_projects.xlsx` | `expansion_monitor.py` | 正式项目结果 | 中高；读取历史合并后写回，读失败时可能重建 |
| `high_value_leads.xlsx` | `high_value_filter.py` | 业务数据/派生结果 | 高；每次根据主结果重算并覆盖 |
| `customer_pool.xlsx` | `customer_pool.py`、`followup_manager.py`、`candidate_contact_importer.py` | 业务数据 | 高；多个脚本会写同一文件，字段补齐和联系方式导入均会改写 |
| `followup_tasks.xlsx` | `followup_manager.py` | 业务数据/派生结果 | 高；每次重算并覆盖 |
| `customer_contact_candidates.xlsx` | `contact_finder.py` | 业务数据/候选结果 | 高；每次搜索结果直接覆盖 |
| `enterprise_candidates.xlsx` | `source_discovery.py`、`candidate_ranker.py` | 业务数据/候选结果 | 中高；发现脚本合并写回，排序脚本直接写回同文件 |
| `enterprise_url_status.xlsx` | `enterprise_source_manager.py`、`candidate_importer.py`、`enterprise_validator.py` | 业务数据/状态表 | 高；多个脚本直接更新同一状态表 |
| `target_companies.xlsx` | `target_company_manager.py` | 业务数据 | 中；会合并种子企业后写回 |
| `manual_import.xlsx` | `manual_import.py` | 手工模板/输入数据 | 中；模板不存在时创建，直接运行模板创建函数会覆盖空模板 |
| `test_output/test_bid_results.xlsx` | `test_sample_run.py` | 测试数据 | 低；写入隔离测试目录 |
| `test_output/test_daily_report.txt` | `test_sample_run.py`/`reporter.py` | 测试数据 | 低；写入隔离测试目录 |

当前目录中还存在 `enterprise_url_status.*.xlsx` 备份/历史状态文件，静态代码未发现会自动生成这些备份文件。

## 4. 静态问题检查

### 绝对路径和旧目录路径

- Python 文件中未发现硬编码的 `D:\...`、`C:\...`、`D:\Codex\MarbleFinder\BidRadar` 或 `D:\AI-Workspace\01_BidRadar_招标雷达` 路径。
- `WORK_LOG.md` 中记录了旧源目录和当前目标目录，仅为迁移记录，不影响运行。
- `browser_runner.py` 会通过环境变量拼接 Chrome/Edge 常见安装路径，不是项目旧目录。

### 固定文件名

大量模块使用当前工作目录下的固定文件名，例如 `bid_results.xlsx`、`customer_pool.xlsx`、`enterprise_url_status.xlsx`。这使脚本简单，但也要求运行前确认工作目录，且不利于区分正式、调试、测试输出。

### 直接覆盖 Excel/TXT

- 直接覆盖 TXT：`reporter.py` 写 `daily_report.txt`，`eia_debug.py` 写 `eia_diagnosis.txt`。
- 直接覆盖调试 Excel：`debug_raw_results.py`、`jianyu_search.py`、`eia_debug.py`、`project_monitor.py` 的 debug 输出。
- 多数业务 Excel 会读取历史后合并再写回，但仍是同名写回；如果历史读取失败，部分模块会用空表继续生成，存在数据丢失风险。
- `customer_pool.xlsx` 和 `enterprise_url_status.xlsx` 风险最高，因为多个脚本会改写同一个业务状态表。

### 重复功能模块

- `project_monitor.py`、`eia_monitor.py`、`expansion_monitor.py` 存在大量相似的联网、解析、去重、历史合并、评分、地区识别逻辑。
- `source_discovery.py` 和 `contact_finder.py` 都实现了 Bing 搜索、结果解析、公开 URL 判断和候选 Excel 导出逻辑。
- `manual_import.py`、`jianyu_importer.py`、`exporter.py` 都处理主招标结果唯一 ID、历史合并和写回。
- `main.py` 和 `test_sample_run.py` 都有一套构建招标结果、地区识别、行业过滤和评分逻辑，测试入口为隔离安全做了合理复制，但后续可能出现逻辑漂移。

### 未被引用的脚本

按静态 import 关系看，以下文件主要作为独立脚本入口存在，未被其他模块导入：`candidate_contact_importer.py`、`candidate_importer.py`、`candidate_ranker.py`、`contact_finder.py`、`customer_pool.py`、`debug_raw_results.py`、`enterprise_source_manager.py`、`enterprise_validator.py`、`expansion_monitor.py`、`followup_manager.py`、`high_value_filter.py`、`jianyu_importer.py`、`jianyu_search.py`、`manual_import.py`、`project_monitor.py`、`source_discovery.py`、`target_company_manager.py`。

`commercial_sources.py` 当前未发现被任何 Python 文件引用，可能是历史或预留配置。

## 5. 网络访问模块汇总

直接或入口间接可能访问网络的 Python 文件共 13 个：

- `main.py`：默认 `USE_SAMPLE_DATA = False`，会调用 `crawler.py`。
- `crawler.py`
- `debug_raw_results.py`
- `project_monitor.py`
- `eia_monitor.py`
- `eia_debug.py`：缺少 `eia_raw_results.xlsx` 时会联网。
- `expansion_monitor.py`
- `enterprise_crawler.py`
- `enterprise_validator.py`
- `source_discovery.py`
- `contact_finder.py`
- `browser_runner.py`
- `jianyu_search.py`

仅包含 URL 配置但自身不发请求的文件未计入上面数量，例如 `sources.py`、`project_sources.py`、`eia_sources.py`、`expansion_sources.py`、`enterprise_sources.py`、`commercial_sources.py`、`sample_data.py`。

## 6. 写入文件模块汇总

可能写入 Excel/TXT 的 Python 文件共 23 个：

- `main.py`
- `exporter.py`
- `reporter.py`
- `project_monitor.py`
- `eia_monitor.py`
- `expansion_monitor.py`
- `enterprise_source_manager.py`
- `enterprise_validator.py`
- `source_discovery.py`
- `candidate_importer.py`
- `candidate_ranker.py`
- `contact_finder.py`
- `candidate_contact_importer.py`
- `customer_pool.py`
- `followup_manager.py`
- `high_value_filter.py`
- `manual_import.py`
- `jianyu_search.py`
- `jianyu_importer.py`
- `debug_raw_results.py`
- `eia_debug.py`
- `target_company_manager.py`
- `test_sample_run.py`

## 7. 优先整理建议

1. 先统一输出目录和运行模式保护：将正式结果、调试结果、业务状态、测试输出分目录管理，并在联网脚本和写正式文件脚本前增加明确确认或 dry-run 入口。
2. 优先保护共享业务状态表：`customer_pool.xlsx` 和 `enterprise_url_status.xlsx` 都被多个脚本写入，建议建立自动备份、写入前校验、写入后摘要和失败回滚策略。
3. 抽取重复的数据流工具：公开搜索、Excel 历史合并、唯一 ID、固定列补齐、URL 判断等逻辑重复较多，后续可合并到公共模块，降低不同入口行为漂移风险。
