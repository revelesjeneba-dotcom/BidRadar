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
from scoring import score_bid


MANUAL_IMPORT_FILE = "manual_import.xlsx"

MANUAL_COLUMNS = [
    "标题",
    "链接",
    "发布日期",
    "采购单位",
    "省份",
    "城市",
    "公告类型",
    "预算金额",
    "关键词",
    "备注",
]


def create_manual_template(import_file=MANUAL_IMPORT_FILE):
    template_df = pd.DataFrame(columns=MANUAL_COLUMNS)
    template_df.to_excel(import_file, index=False, engine="openpyxl")
    print("[DONE] Created manual_import.xlsx template")
    return import_file


def import_manual_bids(
    import_file=MANUAL_IMPORT_FILE,
    output_file=OUTPUT_FILE,
):
    if not os.path.exists(import_file):
        create_manual_template(import_file)

    manual_df = pd.read_excel(import_file)
    manual_df = _ensure_manual_columns(manual_df)
    existing_df = _read_or_create_results(output_file)

    for column in EXPORT_COLUMNS:
        if column not in existing_df.columns:
            existing_df[column] = ""

    if not existing_df.empty:
        existing_df["唯一ID"] = existing_df.apply(
            lambda row: _existing_or_manual_unique_id(row),
            axis=1,
        )
        existing_df = existing_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )
        existing_df["是否新增"] = "否"

    existing_ids = set(existing_df["唯一ID"].fillna("").astype(str))
    new_records = []
    skipped = 0
    collected_date = date.today().strftime("%Y-%m-%d")

    for _, row in manual_df.iterrows():
        record = _build_record(row, collected_date)

        if not record["招标标题"] and not record["链接"]:
            continue

        unique_id = make_manual_unique_id(record)

        if unique_id in existing_ids:
            skipped += 1
            continue

        record["唯一ID"] = unique_id
        scoring = score_bid(record)
        record["价值分数"] = scoring["score"]
        record["价值等级"] = scoring["level"]
        record["推荐跟进"] = scoring["recommend"]
        record["跟进优先级"] = scoring["priority"]

        new_records.append(record)
        existing_ids.add(unique_id)

    new_df = pd.DataFrame(new_records)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    for column in EXPORT_COLUMNS:
        if column not in combined_df.columns:
            combined_df[column] = ""

    combined_df = combined_df[EXPORT_COLUMNS]
    combined_df.to_excel(output_file, index=False, engine="openpyxl")

    print(f"导入数量：{len(new_records)}")
    print(f"重复跳过：{skipped}")
    print(f"最终总数：{len(combined_df)}")

    return {
        "imported": len(new_records),
        "skipped": skipped,
        "total": len(combined_df),
        "output_file": output_file,
    }


def _ensure_manual_columns(df):
    for column in MANUAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df[MANUAL_COLUMNS]


def _read_or_create_results(output_file):
    if not os.path.exists(output_file):
        empty_df = pd.DataFrame(columns=EXPORT_COLUMNS)
        empty_df.to_excel(output_file, index=False, engine="openpyxl")
        return empty_df

    try:
        return pd.read_excel(output_file)
    except Exception as error:
        print(f"[ERROR] Failed to read existing results; recreating: {error}")
        return pd.DataFrame(columns=EXPORT_COLUMNS)


def _build_record(row, collected_date):
    title = clean_cell(row.get("标题", ""))
    keyword = clean_cell(row.get("关键词", ""))

    return {
        "唯一ID": "",
        "是否新增": "是",
        "采集日期": collected_date,
        "搜索关键词": keyword,
        "省份": clean_cell(row.get("省份", "")),
        PROVINCE_CONFIDENCE_COLUMN: "manual",
        "城市": clean_cell(row.get("城市", "")),
        "招标标题": title,
        "采购单位": clean_cell(row.get("采购单位", "")),
        "公告类型": clean_cell(row.get("公告类型", "")),
        "发布日期": clean_cell(row.get("发布日期", "")),
        "截止日期": "",
        "预算金额": clean_cell(row.get("预算金额", "")),
        "信息来源": "人工导入",
        "链接": clean_cell(row.get("链接", "")),
        "匹配关键词": keyword,
        "价值分数": "",
        "价值等级": "",
        "推荐跟进": "",
        "跟进优先级": "",
        "跟进状态": "待跟进",
        "备注": "剑鱼标讯人工导入",
    }


def make_manual_unique_id(record):
    link = clean_cell(record.get("链接", ""))

    if link:
        return f"link:{link}"

    title = clean_cell(record.get("招标标题", ""))
    publish_date = clean_cell(record.get("发布日期", ""))
    return f"title:{title}+date:{publish_date}"


def _existing_or_manual_unique_id(row):
    unique_id = clean_cell(row.get("唯一ID", ""))

    if unique_id:
        return unique_id

    return make_manual_unique_id(row.to_dict())


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    import_manual_bids()
