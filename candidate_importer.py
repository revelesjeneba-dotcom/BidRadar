"""
BidRadar V2.4 confirmed candidate importer.

Imports manually confirmed candidate procurement URLs from
enterprise_candidates.xlsx into enterprise_url_status.xlsx.
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import os

import pandas as pd


CANDIDATES_FILE = "enterprise_candidates.xlsx"
STATUS_FILE = "enterprise_url_status.xlsx"

CONFIRMED_VALUE = "是"
SKIP_REMARK = "已有采购平台网址，跳过"
IMPORT_REMARK = "从候选入口导入，待验证"

REQUIRED_CANDIDATE_COLUMNS = [
    "企业名称",
    "候选网址",
    "是否确认",
]

REQUIRED_STATUS_COLUMNS = [
    "企业名称",
    "采购平台网址",
    "是否验证",
    "备注",
]


def import_confirmed_candidates(
    candidates_file=CANDIDATES_FILE,
    status_file=STATUS_FILE,
):
    """Import confirmed candidate URLs into enterprise_url_status.xlsx."""
    if not os.path.exists(candidates_file):
        print(f"[ERROR] Candidate file not found: {candidates_file}")
        return {
            "imported": 0,
            "skipped": 0,
            "unmatched": 0,
        }

    if not os.path.exists(status_file):
        print(f"[ERROR] Enterprise status file not found: {status_file}")
        return {
            "imported": 0,
            "skipped": 0,
            "unmatched": 0,
        }

    candidates_df = pd.read_excel(candidates_file)
    status_df = pd.read_excel(status_file)

    ensure_columns(candidates_df, REQUIRED_CANDIDATE_COLUMNS)
    ensure_columns(status_df, REQUIRED_STATUS_COLUMNS)
    prepare_text_columns(candidates_df, REQUIRED_CANDIDATE_COLUMNS)
    prepare_text_columns(status_df, REQUIRED_STATUS_COLUMNS)

    confirmed_df = candidates_df[
        candidates_df["是否确认"].apply(clean_cell) == CONFIRMED_VALUE
    ].copy()

    imported = 0
    skipped = 0
    unmatched = 0

    for _, candidate in confirmed_df.iterrows():
        enterprise_name = clean_cell(candidate.get("企业名称", ""))
        candidate_url = clean_cell(candidate.get("候选网址", ""))

        if not enterprise_name or not candidate_url:
            unmatched += 1
            continue

        matched_indexes = status_df.index[
            status_df["企业名称"].apply(clean_cell) == enterprise_name
        ].tolist()

        if not matched_indexes:
            unmatched += 1
            continue

        row_index = matched_indexes[0]
        existing_url = clean_cell(status_df.at[row_index, "采购平台网址"])

        if existing_url:
            status_df.at[row_index, "备注"] = SKIP_REMARK
            skipped += 1
            continue

        status_df.at[row_index, "采购平台网址"] = candidate_url
        status_df.at[row_index, "是否验证"] = "否"
        status_df.at[row_index, "备注"] = IMPORT_REMARK
        imported += 1

    status_df.to_excel(status_file, index=False, engine="openpyxl")

    print(f"[DONE] Imported: {imported}")
    print(f"[DONE] Skipped: {skipped}")
    print(f"[DONE] Unmatched enterprises: {unmatched}")

    return {
        "imported": imported,
        "skipped": skipped,
        "unmatched": unmatched,
    }


def ensure_columns(df, columns):
    for column in columns:
        if column not in df.columns:
            df[column] = ""


def prepare_text_columns(df, columns):
    for column in columns:
        df[column] = df[column].astype("object")


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    import_confirmed_candidates()
