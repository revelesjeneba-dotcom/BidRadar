import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date
import os

import pandas as pd

from paths import CUSTOMER_CONTACT_CANDIDATES, CUSTOMER_POOL
from utils.excel_helper import read_excel_safe, write_excel_safe

CANDIDATES_FILE = CUSTOMER_CONTACT_CANDIDATES
CUSTOMER_POOL_FILE = CUSTOMER_POOL

CANDIDATE_COLUMNS = [
    "企业名称",
    "候选网址",
    "候选电话",
    "候选邮箱",
    "搜索关键词",
    "是否确认",
    "备注",
]

POOL_REQUIRED_COLUMNS = [
    "企业名称",
    "官网",
    "电话",
    "邮箱",
    "采购平台网址",
    "备注",
]

CONFIRMED_VALUE = "是"
IMPORT_REMARK_TITLE = "联系方式已确认导入"
PLATFORM_KEYWORDS = [
    "采购平台",
    "供应商平台",
    "SRM",
    "srm",
]


def import_confirmed_contacts(
    candidates_file=CANDIDATES_FILE,
    customer_pool_file=CUSTOMER_POOL_FILE,
):
    if not os.path.exists(candidates_file):
        print(f"[ERROR] Candidates file not found: {candidates_file}")
        return empty_stats(customer_pool_file)

    if not os.path.exists(customer_pool_file):
        print(f"[ERROR] Customer pool file not found: {customer_pool_file}")
        return empty_stats(customer_pool_file)

    candidates_df = read_excel_safe(candidates_file)
    pool_df = read_excel_safe(customer_pool_file)
    candidates_df = ensure_columns(candidates_df, CANDIDATE_COLUMNS)
    pool_df = ensure_columns(pool_df, POOL_REQUIRED_COLUMNS, keep_extra=True)

    total_candidates = len(candidates_df)
    confirmed_df = candidates_df[
        candidates_df["是否确认"].apply(clean_cell) == CONFIRMED_VALUE
    ].copy()

    imported = 0
    skipped = 0
    unmatched = 0
    import_date = date.today().strftime("%Y-%m-%d")

    for _, candidate in confirmed_df.iterrows():
        company_name = clean_cell(candidate.get("企业名称", ""))

        if not company_name:
            skipped += 1
            print("[SKIP] Empty company name")
            continue

        matched_indexes = pool_df.index[
            pool_df["企业名称"].fillna("").astype(str).str.strip() == company_name
        ].tolist()

        if not matched_indexes:
            unmatched += 1
            print(f"[SKIP] Company not found: {company_name}")
            continue

        row_index = matched_indexes[0]
        changed = import_one_contact(pool_df, row_index, candidate)

        if changed:
            append_import_remark(pool_df, row_index, import_date)
            imported += 1
        else:
            skipped += 1
            print(f"[SKIP] No empty fields to update: {company_name}")

    write_excel_safe(
        pool_df,
        customer_pool_file,
        required_columns=POOL_REQUIRED_COLUMNS,
    )

    print(f"[DONE] 总候选数量：{total_candidates}")
    print(f"[DONE] 确认数量：{len(confirmed_df)}")
    print(f"[DONE] 导入数量：{imported}")
    print(f"[DONE] 跳过数量：{skipped}")
    print(f"[DONE] 未匹配数量：{unmatched}")
    print(f"[DONE] 导出文件：{customer_pool_file}")

    return {
        "total_candidates": total_candidates,
        "confirmed": len(confirmed_df),
        "imported": imported,
        "skipped": skipped,
        "unmatched": unmatched,
        "output_file": customer_pool_file,
    }


def import_one_contact(pool_df, row_index, candidate):
    changed = False
    candidate_url = clean_cell(candidate.get("候选网址", ""))
    candidate_phone = clean_cell(candidate.get("候选电话", ""))
    candidate_email = clean_cell(candidate.get("候选邮箱", ""))
    search_keyword = clean_cell(candidate.get("搜索关键词", ""))

    if candidate_phone and is_empty(pool_df.at[row_index, "电话"]):
        pool_df.at[row_index, "电话"] = candidate_phone
        changed = True

    if candidate_email and is_empty(pool_df.at[row_index, "邮箱"]):
        pool_df.at[row_index, "邮箱"] = candidate_email
        changed = True

    if candidate_url:
        url_column = "采购平台网址" if is_platform_keyword(search_keyword) else "官网"

        if is_empty(pool_df.at[row_index, url_column]):
            pool_df.at[row_index, url_column] = candidate_url
            changed = True

    return changed


def append_import_remark(pool_df, row_index, import_date):
    existing_remark = clean_cell(pool_df.at[row_index, "备注"])
    import_remark = f"{IMPORT_REMARK_TITLE}；导入时间：{import_date}"

    if IMPORT_REMARK_TITLE in existing_remark:
        return

    if existing_remark:
        pool_df.at[row_index, "备注"] = f"{existing_remark}；{import_remark}"
    else:
        pool_df.at[row_index, "备注"] = import_remark


def is_platform_keyword(search_keyword):
    return any(keyword in search_keyword for keyword in PLATFORM_KEYWORDS)


def ensure_columns(df, columns, keep_extra=False):
    for column in columns:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].astype("object")

    if keep_extra:
        return df

    return df[columns]


def is_empty(value):
    return clean_cell(value) == ""


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


def empty_stats(output_file):
    return {
        "total_candidates": 0,
        "confirmed": 0,
        "imported": 0,
        "skipped": 0,
        "unmatched": 0,
        "output_file": output_file,
    }


if __name__ == "__main__":
    import_confirmed_contacts()
