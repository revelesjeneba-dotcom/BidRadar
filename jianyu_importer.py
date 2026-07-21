import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date
import os

import pandas as pd

from config import OUTPUT_FILE, PROVINCE_CONFIDENCE_COLUMN
from exporter import EXPORT_COLUMNS
from industry_filter import is_carton_related
from scoring import score_bid
from utils.excel_helper import read_excel_safe, write_excel_safe


RAW_FILE = "raw_jianyu_results.xlsx"

RAW_COLUMNS = [
    "搜索关键词",
    "标题",
    "链接",
    "发布时间",
    "来源",
    "采集时间",
]


def import_jianyu_results(
    raw_file=RAW_FILE,
    output_file=OUTPUT_FILE,
):
    if not os.path.exists(raw_file):
        print(f"[ERROR] Raw Jianyu result file not found: {raw_file}")
        return {
            "raw_count": 0,
            "valid_count": 0,
            "imported": 0,
            "skipped": 0,
            "output_file": output_file,
        }

    raw_df = read_excel_safe(raw_file)
    raw_count = len(raw_df)
    raw_df = ensure_columns(raw_df, RAW_COLUMNS)
    raw_df = deduplicate_raw_rows(raw_df)

    records = []
    collected_date = date.today().strftime("%Y-%m-%d")

    for _, row in raw_df.iterrows():
        record = build_record(row, collected_date)

        if not is_carton_related(record["招标标题"]):
            continue

        record["唯一ID"] = make_jianyu_unique_id(record)

        scoring = score_bid(record)
        record["价值分数"] = scoring["score"]
        record["价值等级"] = scoring["level"]
        record["推荐跟进"] = scoring["recommend"]
        record["跟进优先级"] = scoring["priority"]

        records.append(record)

    current_df = pd.DataFrame(records)

    if not current_df.empty:
        current_df = current_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )

    valid_count = len(current_df)
    history_df = read_history(output_file)

    for column in EXPORT_COLUMNS:
        if column not in history_df.columns:
            history_df[column] = ""

    if not history_df.empty:
        history_df["唯一ID"] = history_df.apply(
            lambda row: existing_or_jianyu_unique_id(row),
            axis=1,
        )
        history_df = history_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )
        history_df["是否新增"] = "否"

    history_ids = set(history_df["唯一ID"].fillna("").astype(str))

    if current_df.empty:
        new_df = pd.DataFrame(columns=EXPORT_COLUMNS)
    else:
        duplicate_mask = current_df["唯一ID"].astype(str).isin(history_ids)
        skipped = int(duplicate_mask.sum())
        new_df = current_df[~duplicate_mask].copy()
        new_df["是否新增"] = "是"

    if current_df.empty:
        skipped = 0

    combined_df = pd.concat([history_df, new_df], ignore_index=True)

    for column in EXPORT_COLUMNS:
        if column not in combined_df.columns:
            combined_df[column] = ""

    combined_df = combined_df[EXPORT_COLUMNS]
    write_excel_safe(
        combined_df,
        output_file,
        required_columns=EXPORT_COLUMNS,
    )

    print(f"原始数量：{raw_count}")
    print(f"有效数量：{valid_count}")
    print(f"新增数量：{len(new_df)}")
    print(f"重复跳过数量：{skipped}")
    print(f"导出文件：{output_file}")

    return {
        "raw_count": raw_count,
        "valid_count": valid_count,
        "imported": len(new_df),
        "skipped": skipped,
        "output_file": output_file,
    }


def ensure_columns(df, columns):
    for column in columns:
        if column not in df.columns:
            df[column] = ""

    return df[columns]


def deduplicate_raw_rows(df):
    seen = set()
    rows = []

    for _, row in df.iterrows():
        title = clean_cell(row.get("标题", ""))
        link = clean_cell(row.get("链接", ""))
        publish_time = clean_cell(row.get("发布时间", ""))

        if link:
            unique_key = f"link:{link}"
        else:
            unique_key = f"title:{title}+time:{publish_time}"

        if unique_key in seen:
            continue

        seen.add(unique_key)
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=df.columns)

    return pd.DataFrame(rows)


def build_record(row, collected_date):
    keyword = clean_cell(row.get("搜索关键词", ""))
    source = clean_cell(row.get("来源", "")) or "剑鱼标讯"

    return {
        "唯一ID": "",
        "是否新增": "是",
        "采集日期": collected_date,
        "搜索关键词": keyword,
        "省份": "",
        PROVINCE_CONFIDENCE_COLUMN: "",
        "城市": "",
        "招标标题": clean_cell(row.get("标题", "")),
        "采购单位": "",
        "公告类型": "",
        "发布日期": clean_cell(row.get("发布时间", "")),
        "截止日期": "",
        "预算金额": "",
        "信息来源": source,
        "链接": clean_cell(row.get("链接", "")),
        "匹配关键词": keyword,
        "价值分数": "",
        "价值等级": "",
        "推荐跟进": "",
        "跟进优先级": "",
        "跟进状态": "待跟进",
        "备注": "剑鱼标讯自动采集",
    }


def read_history(output_file):
    if not os.path.exists(output_file):
        return pd.DataFrame(columns=EXPORT_COLUMNS)

    return read_excel_safe(output_file)


def make_jianyu_unique_id(record):
    link = clean_cell(record.get("链接", ""))

    if link:
        return f"link:{link}"

    title = clean_cell(record.get("招标标题", ""))
    publish_time = clean_cell(record.get("发布日期", ""))
    return f"title:{title}+time:{publish_time}"


def existing_or_jianyu_unique_id(row):
    unique_id = clean_cell(row.get("唯一ID", ""))

    if unique_id:
        return unique_id

    return make_jianyu_unique_id(row.to_dict())


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    import_jianyu_results()
