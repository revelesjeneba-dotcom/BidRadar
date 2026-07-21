"""
BidRadar enterprise source management.

Creates an Excel checklist for enterprise procurement platform URLs.
This module does not crawl or validate any website.
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import datetime
import os

import pandas as pd

from enterprise_sources import ENTERPRISE_SOURCES
from paths import ENTERPRISE_URL_STATUS_FILE
from utils.excel_helper import read_excel_safe, write_excel_safe


OUTPUT_FILE = ENTERPRISE_URL_STATUS_FILE

STATUS_COLUMNS = [
    "企业名称",
    "行业",
    "官网",
    "采购平台网址",
    "优先级",
    "是否公开",
    "需要登录",
    "支持搜索",
    "是否验证",
    "最后检查时间",
    "备注",
]

NEW_STATUS_DEFAULT = "未确认"

PRIORITY_REMARKS = {
    "A": "必监控",
    "B": "推荐监控",
    "C": "观察",
}


def build_enterprise_url_status(sources=None):
    """Build status rows from ENTERPRISE_SOURCES."""
    if sources is None:
        sources = ENTERPRISE_SOURCES

    checked_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []

    for source in sources:
        procurement_url = str(source.get("procurement_url", "")).strip()
        priority = str(source.get("priority", "")).strip().upper()
        remark = PRIORITY_REMARKS.get(priority, "")

        rows.append(
            {
                "企业名称": source.get("name", ""),
                "行业": source.get("industry", ""),
                "官网": source.get("homepage", ""),
                "采购平台网址": procurement_url,
                "优先级": priority,
                "是否公开": NEW_STATUS_DEFAULT,
                "需要登录": NEW_STATUS_DEFAULT,
                "支持搜索": NEW_STATUS_DEFAULT,
                "是否验证": "否",
                "最后检查时间": checked_time,
                "备注": remark,
            }
        )

    return rows


def create_enterprise_url_status_file(output_file=OUTPUT_FILE):
    """Create or update enterprise_url_status.xlsx without overwriting existing data."""
    file_exists = os.path.exists(output_file)
    config_df = pd.DataFrame(build_enterprise_url_status())

    if file_exists:
        df = read_excel_safe(output_file)
        df = _merge_existing_status(df, config_df)
    else:
        df = config_df

    for column in STATUS_COLUMNS:
        if column not in df.columns:
            df[column] = _default_for_column(column)

    write_excel_safe(
        df,
        output_file,
        required_columns=STATUS_COLUMNS,
    )

    action = "Updated" if file_exists else "Created"
    print(f"[DONE] {action} enterprise procurement status file: {output_file}")
    return output_file


def _merge_existing_status(existing_df, config_df):
    for column in STATUS_COLUMNS:
        if column not in existing_df.columns:
            existing_df[column] = _default_for_column(column)

    existing_names = set(existing_df["企业名称"].astype(str))
    missing_rows = config_df[
        ~config_df["企业名称"].astype(str).isin(existing_names)
    ]

    if not missing_rows.empty:
        existing_df = pd.concat(
            [existing_df, missing_rows],
            ignore_index=True,
        )

    return existing_df


def _default_for_column(column):
    if column in ["是否公开", "需要登录", "支持搜索"]:
        return NEW_STATUS_DEFAULT

    return ""


if __name__ == "__main__":
    create_enterprise_url_status_file()
