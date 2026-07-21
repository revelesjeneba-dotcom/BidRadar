# Excel Data Contracts

## Purpose

This document freezes the V6.5.5 Excel structures used as the regression baseline for the V6.6 data-safety upgrade. V6.6 must not change business rules, workbook names, column names, column order, or field meanings.

The contracts describe the first worksheet of each workbook. They do not prescribe formatting, column width, filters, or Excel-internal metadata.

## Data classification

| Workbook | Role | Authority | Producers | Main consumers | Regeneration policy |
|---|---|---|---|---|---|
| `bid_results.xlsx` | Main bid result | Formal historical result | `exporter.py`, `manual_import.py`, `jianyu_importer.py` | `reporter.py`, `high_value_filter.py` | Must preserve readable history |
| `customer_pool.xlsx` | Customer state | Authoritative business state | `customer_pool.py`, `followup_manager.py`, `candidate_contact_importer.py` | Customer and follow-up modules | Must not be rebuilt after a read failure |
| `followup_tasks.xlsx` | Derived follow-up tasks | Derived business result | `followup_manager.py` | Manual follow-up workflow | Regenerable from a valid customer pool |
| `enterprise_url_status.xlsx` | Procurement URL state | Authoritative business state | `enterprise_source_manager.py`, `candidate_importer.py`, `enterprise_validator.py` | Enterprise URL workflow | Must not be rebuilt after a read failure |
| `high_value_leads.xlsx` | Filtered leads | Derived business result | `high_value_filter.py` | `customer_pool.py` | Regenerable from valid bid results |
| `target_companies.xlsx` | Target-company state | Authoritative business input | `target_company_manager.py` | `customer_pool.py` | Preserve manual fields and history |
| `customer_contact_candidates.xlsx` | Contact candidates | Review queue | `contact_finder.py` | `candidate_contact_importer.py` | Regenerable, but confirmations may be manual |

## Frozen column contracts

### `bid_results.xlsx`

Primary deduplication field: `唯一ID`.

```text
唯一ID, 是否新增, 采集日期, 搜索关键词, 省份, 地区识别置信度, 城市,
招标标题, 采购单位, 公告类型, 发布日期, 截止日期, 预算金额, 信息来源,
链接, 匹配关键词, 价值分数, 价值等级, 推荐跟进, 跟进优先级, 跟进状态, 备注
```

### `customer_pool.xlsx`

Business identity field: `企业名称`. The first 16 columns come from `customer_pool.py`; follow-up fields are appended by `followup_manager.py`. `最后跟进日期` is shared and appears only once.

```text
企业名称, 行业, 来源, 招标标题, 省份, 城市, 首次发现日期, 最后跟进日期,
开发状态, 优先级, 价值分数, 官网, 电话, 邮箱, 采购平台网址, 备注,
首次联系日期, 下次跟进日期, 跟进次数, 跟进状态, 最近跟进记录
```

### `followup_tasks.xlsx`

```text
企业名称, 行业, 电话, 邮箱, 开发状态, 最后跟进日期, 未跟进天数,
提醒等级, 建议动作, 备注
```

### `enterprise_url_status.xlsx`

Business identity field: `企业名称`. The first 11 columns are created by
`enterprise_source_manager.py`; the remaining validation fields are maintained by
`enterprise_validator.py`. Their order below records the current workbook and must
be preserved during V6.6.

```text
企业名称, 行业, 官网, 采购平台网址, 优先级, 是否公开, 需要登录,
支持搜索, 是否验证, 最后检查时间, 备注, 页面标题, 访问状态, 平台类型,
是否可采集, 验证结果, HTTP状态码, 是否跳转
```

### `high_value_leads.xlsx`

```text
推荐等级, 招标标题, 采购单位, 省份, 城市, 价值分数,
推荐跟进, 跟进优先级, 链接, 推荐动作
```

### `target_companies.xlsx`

Business identity field: `企业名称`.

```text
企业名称, 行业, 省份, 城市, 官网, 采购平台网址, 联系人, 电话,
邮箱, 监控方式, 优先级, 状态, 最后检查时间, 备注
```

### `customer_contact_candidates.xlsx`

```text
企业名称, 搜索关键词, 候选标题, 候选网址, 候选电话, 候选邮箱,
来源, 是否确认, 备注
```

## V6.6-01 regression baseline

The offline baseline uses `sample_data.py` and calls only in-memory transformation functions. It must not call a crawler or write a workbook.

Expected sample statistics:

- Raw records: 7
- Filtered and deduplicated records: 5
- Unique IDs: 5
- Levels: `★=2`, `★★=1`, `★★★=1`, `★★★★★=1`
- Priorities: `观察=2`, `低=1`, `中=1`, `最高=1`

Tests also freeze scoring boundaries at 0, 30, 50, 70, and 90 points.

## Test command

Run without bytecode output:

```text
python -B -m unittest discover -s tests -v
```

If the local command is `python3`, use:

```text
python3 -B -m unittest discover -s tests -v
```

The workbook contract test uses only the Python standard library and opens existing `.xlsx` files as ZIP/XML input. The in-memory pipeline test is skipped when project runtime dependencies are unavailable.

## Change control

Changing a frozen contract requires an explicit versioned data migration. It must not be bundled into the V6.6 safety refactor. Any future change must document compatibility, migration, rollback, and before/after validation.
