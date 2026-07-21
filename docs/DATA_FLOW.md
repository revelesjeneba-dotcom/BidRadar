# Data Flow

## 总览

```text
数据来源
  -> 采集
  -> 导入
  -> 过滤
  -> 评分
  -> 主结果
  -> 高价值线索
  -> 客户池
  -> 跟进
  -> CRM
```

## 数据来源

- 公开招标网页：`sources.py` -> `crawler.py`
- 生产项目公开搜索：`project_sources.py` -> `project_monitor.py`
- 环评项目公开搜索：`eia_sources.py` -> `eia_monitor.py`
- 扩产项目公开页面：`expansion_sources.py` -> `expansion_monitor.py`
- 企业采购入口：`enterprise_sources.py` 及相关企业入口脚本
- 手工数据：`manual_import.xlsx`
- 剑鱼 raw 数据：`raw_jianyu_results.xlsx`
- 本地模拟数据：`sample_data.py`

## 采集

- `main.py` 默认调用 `crawler.py` 采集公开招标。
- `project_monitor.py`、`eia_monitor.py`、`expansion_monitor.py` 采集项目线索。
- `jianyu_search.py` 通过 Playwright 获取剑鱼 raw 结果。
- `contact_finder.py` 通过公开搜索找联系方式候选。

## 导入

- `manual_import.py` 将人工表导入主结果。
- `jianyu_importer.py` 将剑鱼 raw 结果导入主结果。
- `candidate_importer.py` 将确认的企业入口导入状态表。
- `candidate_contact_importer.py` 将确认的联系方式导入客户池。

## 主招标结果写入保护（V6.6-03）

```text
exporter.py / manual_import.py / jianyu_importer.py
  -> 读取已有 bid_results.xlsx（读取失败则停止）
  -> 保持原有合并、唯一 ID 和去重逻辑
  -> 写入同目录临时 Excel
  -> 回读验证列顺序和行数
  -> 备份已有 bid_results.xlsx
  -> 原子替换正式文件
```

`bid_results.xlsx` 不存在时允许创建。正式文件存在但损坏、被锁定或无法
读取时，不允许以空历史继续写入。V6.6-03 没有改变主招标结果的列结构和
业务数据流。

## 客户池和跟进任务写入保护（V6.6-04）

```text
high_value_leads.xlsx + target_companies.xlsx
  -> customer_pool.py（保留未知人工字段和原列顺序）
  -> 安全写入 customer_pool.xlsx

customer_contact_candidates.xlsx
  -> candidate_contact_importer.py
  -> 安全写入 customer_pool.xlsx

customer_pool.xlsx
  -> followup_manager.py（内存生成客户池补充字段和任务表）
  -> 分别备份两个已有输出
  -> 安全写入 customer_pool.xlsx 和 followup_tasks.xlsx
  -> 任一失败时恢复两份旧文件
```

自动恢复失败时，错误信息会给出本次客户池与任务表备份路径。人工恢复方式是
停止所有相关脚本，将对应备份文件复制回原文件位置，再核对列结构和文件哈希。
V6.6-04 不改变客户匹配、客户更新、联系方式导入或跟进任务生成规则。

## 评分

- `scoring.py` 为主招标线索评分。
- 项目监控脚本各自包含项目评分逻辑。
- `candidate_ranker.py` 为企业入口候选评分。

## 客户池

```text
bid_results.xlsx
  -> high_value_filter.py
  -> high_value_leads.xlsx
  -> customer_pool.py
  -> customer_pool.xlsx
```

`target_companies.xlsx` 为客户池补充行业、官网、采购平台、电话和邮箱。

## 跟进

```text
customer_pool.xlsx
  -> followup_manager.py
  -> followup_tasks.xlsx
```

## CRM

当前项目内尚未接入外部 CRM。现阶段 CRM 交付形态是 `customer_pool.xlsx` 和 `followup_tasks.xlsx`，后续可作为 CRM 导入源。
