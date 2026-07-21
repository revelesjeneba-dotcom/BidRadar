# Architecture

本文基于 `FILE_MAP.md` 整理 PackagingRadar 当前模块结构、数据流和 Excel 流向。

## 模块关系图

```text
sources.py / enterprise_sources.py / *_sources.py
        |
        v
crawler.py / project_monitor.py / eia_monitor.py / expansion_monitor.py
        |
        v
filtering + scoring
        |
        v
exporter.py / module-specific exporters
        |
        v
Excel results -> high_value_filter.py -> customer_pool.py -> followup_manager.py
```

## 数据流

```text
公开网页 / 手工表 / 剑鱼 raw / 企业候选
    -> 采集或导入
    -> 行业过滤
    -> 地区识别
    -> 评分和推荐
    -> Excel 输出
    -> 高价值线索
    -> 客户池
    -> 跟进任务
```

## Excel 流向

```text
bid_results.xlsx
    -> high_value_leads.xlsx
    -> customer_pool.xlsx
    -> followup_tasks.xlsx

target_companies.xlsx
    -> customer_pool.xlsx

customer_contact_candidates.xlsx
    -> customer_pool.xlsx

enterprise_candidates.xlsx
    -> enterprise_url_status.xlsx

enterprise_url_status.xlsx
    -> enterprise_validator.py 写回验证状态
```

## Python 模块关系

- `main.py` 调用 `crawler.py`、`exporter.py`、`reporter.py`、`industry_filter.py`、`scoring.py`。
- `crawler.py` 读取 `sources.py`。
- `high_value_filter.py` 读取主结果并输出高价值线索。
- `customer_pool.py` 读取高价值线索、目标企业和已有客户池，写回客户池。
- `followup_manager.py` 读取并写回客户池，同时生成跟进任务。
- `candidate_contact_importer.py` 读取联系方式候选并写回客户池。
- 企业入口模块围绕 `enterprise_sources.py`、`enterprise_candidates.xlsx`、`enterprise_url_status.xlsx` 工作。
- 项目监控模块按生产、环评、扩产拆分，各自读取 sources/keywords 并写入对应 Excel。

## 主流程

```text
python main.py
    -> 判断 USE_SAMPLE_DATA
    -> 采集公开网页或读取 sample_data
    -> build_results
    -> export_to_excel
    -> generate_daily_report
```

当前默认模式为公开网页采集。运行前必须确认是否允许联网和写正式结果。

## 路径层（V6.6-08）

```text
paths.py / PROJECT_ROOT
    ├─ 正式结果与业务状态
    ├─ 企业候选与联系方式候选
    ├─ 生产、环评、扩产项目结果
    ├─ raw/debug Excel
    ├─ 手工导入 Excel
    └─ 日报与诊断 TXT
```

业务脚本不再根据进程当前工作目录拼接正式数据路径。所有登记路径都基于
`paths.py` 自身位置计算，因此从其他工作目录启动时仍指向项目根目录。
V6.6-08 没有移动文件或改变默认输出位置。
