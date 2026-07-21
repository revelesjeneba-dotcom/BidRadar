import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date
import os

import pandas as pd

from paths import CUSTOMER_POOL, HIGH_VALUE_LEADS, TARGET_COMPANIES
from utils.excel_helper import read_excel_safe, write_excel_safe

HIGH_VALUE_FILE = HIGH_VALUE_LEADS
TARGET_COMPANY_FILE = TARGET_COMPANIES
OUTPUT_FILE = CUSTOMER_POOL

CUSTOMER_COLUMNS = [
    "企业名称",
    "行业",
    "来源",
    "招标标题",
    "省份",
    "城市",
    "首次发现日期",
    "最后跟进日期",
    "开发状态",
    "优先级",
    "价值分数",
    "官网",
    "电话",
    "邮箱",
    "采购平台网址",
    "备注",
]

HIGH_VALUE_COLUMNS = [
    "推荐等级",
    "招标标题",
    "采购单位",
    "省份",
    "城市",
    "价值分数",
    "推荐跟进",
    "跟进优先级",
    "链接",
    "推荐动作",
]

TARGET_COLUMNS = [
    "企业名称",
    "行业",
    "官网",
    "采购平台网址",
    "电话",
    "邮箱",
]


def build_customer_pool(
    high_value_file=HIGH_VALUE_FILE,
    target_company_file=TARGET_COMPANY_FILE,
    output_file=OUTPUT_FILE,
):
    high_value_df = read_excel_or_empty(high_value_file, HIGH_VALUE_COLUMNS)
    target_df = read_excel_or_empty(target_company_file, TARGET_COLUMNS)
    pool_df = read_excel_or_empty(output_file, CUSTOMER_COLUMNS)

    high_value_df = ensure_columns(high_value_df, HIGH_VALUE_COLUMNS)
    target_df = ensure_columns(target_df, TARGET_COLUMNS)
    pool_df = ensure_columns(pool_df, CUSTOMER_COLUMNS, keep_extra=True)

    target_map = build_target_map(target_df)
    today = date.today().strftime("%Y-%m-%d")
    existing_names = set(
        pool_df["企业名称"].fillna("").astype(str).str.strip()
    )
    processed_names = set()
    new_count = 0
    existing_count = 0

    pool_df = pool_df.copy()

    for _, lead in high_value_df.iterrows():
        company_name = clean_cell(lead.get("采购单位", ""))

        if not company_name:
            continue

        if company_name in processed_names:
            pool_df = update_existing_customer(pool_df, lead, target_map, company_name, today)
            continue

        processed_names.add(company_name)

        if company_name in existing_names:
            pool_df = update_existing_customer(pool_df, lead, target_map, company_name, today)
            existing_count += 1
            continue

        new_row = build_new_customer(lead, target_map, company_name, today)
        pool_df = pd.concat([pool_df, pd.DataFrame([new_row])], ignore_index=True)
        existing_names.add(company_name)
        new_count += 1

    pool_df = ensure_columns(pool_df, CUSTOMER_COLUMNS, keep_extra=True)
    pool_df = pool_df.drop_duplicates(subset=["企业名称"], keep="first")
    pool_df["_sort_score"] = pool_df["价值分数"].apply(parse_score)
    pool_df = pool_df.sort_values(by="_sort_score", ascending=False)
    pool_df = pool_df.drop(columns=["_sort_score"])
    write_excel_safe(
        pool_df,
        output_file,
        required_columns=CUSTOMER_COLUMNS,
    )

    print(f"总客户数：{len(pool_df)}")
    print(f"新增客户：{new_count}")
    print(f"已存在客户：{existing_count}")
    print(f"导出文件：{output_file}")

    return {
        "total": len(pool_df),
        "new": new_count,
        "existing": existing_count,
        "output_file": output_file,
    }


def build_new_customer(lead, target_map, company_name, today):
    target = target_map.get(company_name, {})

    return {
        "企业名称": company_name,
        "行业": clean_cell(target.get("行业", "")),
        "来源": "高价值线索",
        "招标标题": clean_cell(lead.get("招标标题", "")),
        "省份": clean_cell(lead.get("省份", "")),
        "城市": clean_cell(lead.get("城市", "")),
        "首次发现日期": today,
        "最后跟进日期": "",
        "开发状态": "待开发",
        "优先级": "高",
        "价值分数": parse_score(lead.get("价值分数", "")),
        "官网": clean_cell(target.get("官网", "")),
        "电话": clean_cell(target.get("电话", "")),
        "邮箱": clean_cell(target.get("邮箱", "")),
        "采购平台网址": clean_cell(target.get("采购平台网址", "")),
        "备注": "",
    }


def update_existing_customer(pool_df, lead, target_map, company_name, today):
    indexes = pool_df.index[
        pool_df["企业名称"].fillna("").astype(str).str.strip() == company_name
    ].tolist()

    if not indexes:
        return pool_df

    row_index = indexes[0]
    target = target_map.get(company_name, {})
    lead_score = parse_score(lead.get("价值分数", ""))
    existing_score = parse_score(pool_df.at[row_index, "价值分数"])

    pool_df.at[row_index, "来源"] = merge_source(
        pool_df.at[row_index, "来源"],
        "高价值线索",
    )
    pool_df.at[row_index, "招标标题"] = clean_cell(lead.get("招标标题", ""))
    pool_df.at[row_index, "省份"] = prefer_existing(
        pool_df.at[row_index, "省份"],
        lead.get("省份", ""),
    )
    pool_df.at[row_index, "城市"] = prefer_existing(
        pool_df.at[row_index, "城市"],
        lead.get("城市", ""),
    )
    pool_df.at[row_index, "价值分数"] = max(existing_score, lead_score)

    fill_from_target(pool_df, row_index, target)

    if not clean_cell(pool_df.at[row_index, "首次发现日期"]):
        pool_df.at[row_index, "首次发现日期"] = today

    return pool_df


def fill_from_target(pool_df, row_index, target):
    for column in ["行业", "官网", "电话", "邮箱", "采购平台网址"]:
        if not clean_cell(pool_df.at[row_index, column]):
            pool_df.at[row_index, column] = clean_cell(target.get(column, ""))


def build_target_map(target_df):
    target_map = {}

    for _, row in target_df.iterrows():
        company_name = clean_cell(row.get("企业名称", ""))

        if not company_name or company_name in target_map:
            continue

        target_map[company_name] = row.to_dict()

    return target_map


def read_excel_or_empty(path, columns):
    if not os.path.exists(path):
        return pd.DataFrame(columns=columns)

    return read_excel_safe(path)


def ensure_columns(df, columns, keep_extra=False):
    original_columns = list(df.columns)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    for column in columns:
        df[column] = df[column].astype("object")

    if keep_extra:
        appended_columns = [
            column for column in columns if column not in original_columns
        ]
        return df[original_columns + appended_columns]

    return df[columns]


def merge_source(existing_value, new_value):
    existing = clean_cell(existing_value)

    if not existing:
        return new_value

    sources = [source.strip() for source in existing.split("、") if source.strip()]

    if new_value not in sources:
        sources.append(new_value)

    return "、".join(sources)


def prefer_existing(existing_value, new_value):
    existing = clean_cell(existing_value)

    if existing:
        return existing

    return clean_cell(new_value)


def parse_score(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    build_customer_pool()
