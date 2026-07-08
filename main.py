import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date

import pandas as pd

from config import (
    ALLOW_UNKNOWN_PROVINCE,
    INDUSTRY_KEYWORDS,
    OUTPUT_FILE,
    PROJECT_CN_NAME,
    PROVINCE_CONFIDENCE_COLUMN,
    PROVINCE_ALIASES,
    PROVINCE_TEXT_ALIASES,
    PROVINCES,
    SOURCE_PROVINCE_RULES,
)
from crawler import crawl_all_sources
from exporter import EXPORT_COLUMNS, export_to_excel, make_unique_id
from industry_filter import is_carton_related
from reporter import generate_daily_report
from sample_data import get_sample_bids
from scoring import score_bid


# True：使用本地模拟数据，适合新手测试。
# False：使用 crawler.py 采集公开网页，失败时会自动跳过。
USE_SAMPLE_DATA = False

def find_matched_keywords(title):
    return [
        keyword
        for keyword in INDUSTRY_KEYWORDS
        if keyword in title
    ]


def detect_province(bid):
    """识别省份，并给出地区识别置信度。"""
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


def build_results(raw_bids):
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

        # 模拟数据通常有省份字段；真实网页可能只在标题中出现地区。
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


def main():
    print("=" * 50)
    print(PROJECT_CN_NAME)
    print("=" * 50)

    if USE_SAMPLE_DATA:
        print("[MODE] Sample data")
        raw_bids = get_sample_bids()
    else:
        print("[MODE] Public web collection")
        raw_bids = crawl_all_sources()

    results = build_results(raw_bids)
    export_to_excel(results, OUTPUT_FILE)
    generate_daily_report(OUTPUT_FILE)

    print(f"[DONE] Raw records: {len(raw_bids)}")
    print(f"[DONE] Filtered records: {len(results)}")
    print(f"[DONE] Export file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
