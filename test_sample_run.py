import os
import socket
import sys
from collections import Counter
from datetime import date

import pandas as pd

from config import (
    ALLOW_UNKNOWN_PROVINCE,
    INDUSTRY_KEYWORDS,
    PROVINCE_ALIASES,
    PROVINCE_CONFIDENCE_COLUMN,
    PROVINCE_TEXT_ALIASES,
    PROVINCES,
    SOURCE_PROVINCE_RULES,
)
from exporter import EXPORT_COLUMNS, make_unique_id
from industry_filter import is_carton_related
from reporter import generate_daily_report
from sample_data import get_sample_bids
from scoring import score_bid


OUTPUT_DIR = "test_output"
TEST_EXCEL_FILE = os.path.join(OUTPUT_DIR, "test_bid_results.xlsx")
TEST_REPORT_FILE = os.path.join(OUTPUT_DIR, "test_daily_report.txt")

NETWORK_ATTEMPTS = []
_ORIGINAL_SOCKET = socket.socket
_ORIGINAL_CREATE_CONNECTION = socket.create_connection


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


class NetworkBlockedError(RuntimeError):
    pass


class GuardedSocket(socket.socket):
    def connect(self, address):
        NETWORK_ATTEMPTS.append(("socket.connect", address))
        raise NetworkBlockedError(f"Network access is blocked: {address}")

    def connect_ex(self, address):
        NETWORK_ATTEMPTS.append(("socket.connect_ex", address))
        raise NetworkBlockedError(f"Network access is blocked: {address}")


def guarded_create_connection(address, *args, **kwargs):
    NETWORK_ATTEMPTS.append(("socket.create_connection", address))
    raise NetworkBlockedError(f"Network access is blocked: {address}")


def install_network_guard():
    socket.socket = GuardedSocket
    socket.create_connection = guarded_create_connection


def restore_network_guard():
    socket.socket = _ORIGINAL_SOCKET
    socket.create_connection = _ORIGINAL_CREATE_CONNECTION


def find_matched_keywords(title):
    return [
        keyword
        for keyword in INDUSTRY_KEYWORDS
        if keyword in title
    ]


def detect_province(bid):
    source = str(bid.get("信息来源", ""))

    for source_keyword, province_name in SOURCE_PROVINCE_RULES.items():
        if source_keyword in source:
            return province_name, "high"

    text = " ".join(
        [
            str(bid.get("省份", "")),
            str(bid.get("城市", "")),
            str(bid.get("招标标题", "")),
            str(bid.get("采购单位", "")),
            str(bid.get("公告类型", "")),
            str(bid.get("备注", "")),
        ]
    )

    for province, aliases in PROVINCE_ALIASES.items():
        if any(alias in text for alias in aliases):
            return province, "medium"

    for province, aliases in PROVINCE_TEXT_ALIASES.items():
        if any(alias in text for alias in aliases):
            return province, "medium"

    return "", "unknown"


def build_sample_results(raw_bids):
    results = []
    collected_date = date.today().strftime("%Y-%m-%d")

    for bid in raw_bids:
        title = str(bid.get("招标标题", "")).strip()
        province, province_confidence = detect_province(bid)
        text_for_match = " ".join(
            [
                str(bid.get("省份", "")),
                str(bid.get("城市", "")),
                title,
            ]
        )

        old_region_matched = any(
            province_name in text_for_match
            for province_name in PROVINCES
        )

        if (
            not old_region_matched
            and province_confidence == "unknown"
            and not ALLOW_UNKNOWN_PROVINCE
        ):
            continue

        industry_text = " ".join(
            [
                title,
                str(bid.get("采购单位", "")),
                str(bid.get("公告类型", "")),
                str(bid.get("备注", "")),
            ]
        )

        if not is_carton_related(industry_text):
            continue

        matched_keywords = find_matched_keywords(industry_text)
        scoring = score_bid(bid)

        result = {
            "唯一ID": "",
            "是否新增": "",
            "采集日期": collected_date,
            "搜索关键词": bid.get("搜索关键词", ""),
            "省份": province,
            PROVINCE_CONFIDENCE_COLUMN: province_confidence,
            "城市": bid.get("城市", ""),
            "招标标题": title,
            "采购单位": bid.get("采购单位", ""),
            "公告类型": bid.get("公告类型", ""),
            "发布日期": bid.get("发布日期", ""),
            "截止日期": bid.get("截止日期", ""),
            "预算金额": bid.get("预算金额", ""),
            "信息来源": bid.get("信息来源", ""),
            "链接": bid.get("链接", ""),
            "匹配关键词": "、".join(matched_keywords),
            "价值分数": scoring["score"],
            "价值等级": scoring["level"],
            "推荐跟进": scoring["recommend"],
            "跟进优先级": scoring["priority"],
            "跟进状态": "待跟进",
            "备注": bid.get("备注", ""),
        }
        result["唯一ID"] = make_unique_id(result)
        results.append(result)

    df = pd.DataFrame(results)

    if df.empty:
        return []

    df = df.drop_duplicates(subset=["唯一ID"], keep="first")

    for column in EXPORT_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df[EXPORT_COLUMNS].to_dict("records")


def summarize(results):
    level_counts = Counter(str(row.get("价值等级", "")) for row in results)
    priority_counts = Counter(str(row.get("跟进优先级", "")) for row in results)
    return level_counts, priority_counts


def export_test_results(records, output_file):
    df = pd.DataFrame(records)

    for column in EXPORT_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    if not df.empty:
        df["唯一ID"] = df.apply(lambda row: make_unique_id(row.to_dict()), axis=1)
        df = df.drop_duplicates(subset=["唯一ID"], keep="first")
        df["是否新增"] = "是"

    df = df[EXPORT_COLUMNS]
    df.to_excel(output_file, index=False, engine="openpyxl")
    return output_file


def main():
    install_network_guard()
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        raw_bids = get_sample_bids()
        results = build_sample_results(raw_bids)
        level_counts, priority_counts = summarize(results)

        export_test_results(results, TEST_EXCEL_FILE)
        generate_daily_report(TEST_EXCEL_FILE, TEST_REPORT_FILE)

        print("SAMPLE_RUN_OK")
        print(f"RAW_COUNT={len(raw_bids)}")
        print(f"FILTERED_COUNT={len(results)}")
        print(
            "LEVEL_COUNTS="
            + ";".join(f"{key}:{value}" for key, value in sorted(level_counts.items()))
        )
        print(
            "PRIORITY_COUNTS="
            + ";".join(
                f"{key}:{value}" for key, value in sorted(priority_counts.items())
            )
        )
        print(f"EXCEL_EXISTS={os.path.exists(TEST_EXCEL_FILE)}")
        print(f"REPORT_EXISTS={os.path.exists(TEST_REPORT_FILE)}")
        print(f"NETWORK_ATTEMPTS={len(NETWORK_ATTEMPTS)}")
        print(f"EXCEL_FILE={TEST_EXCEL_FILE}")
        print(f"REPORT_FILE={TEST_REPORT_FILE}")
    finally:
        restore_network_guard()


if __name__ == "__main__":
    main()
