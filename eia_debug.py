import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import datetime
import os
import time

import pandas as pd

import eia_monitor
from eia_sources import EIA_SOURCES


RAW_FILE = "eia_raw_results.xlsx"
DEBUG_FILE = "eia_raw_debug.xlsx"
DIAGNOSIS_FILE = "eia_diagnosis.txt"

EIA_DEBUG_KEYWORDS = [
    "环境影响报告书",
    "环境影响报告表",
    "审批公示",
    "受理公示",
    "拟审批公示",
    "环评公示",
    "环境影响评价",
]

INDUSTRY_DEBUG_KEYWORDS = [
    "食品",
    "饮料",
    "乳业",
    "酒业",
    "食品加工",
    "农副产品加工",
    "预制菜",
    "调味品",
    "粮油",
    "家电",
    "电子",
    "医疗",
    "物流",
    "包装",
]

REGION_DEBUG_KEYWORDS = [
    "江苏",
    "南京",
    "无锡",
    "徐州",
    "常州",
    "苏州",
    "南通",
    "连云港",
    "淮安",
    "盐城",
    "扬州",
    "镇江",
    "泰州",
    "宿迁",
    "安徽",
    "合肥",
    "芜湖",
    "蚌埠",
    "淮南",
    "马鞍山",
    "淮北",
    "铜陵",
    "安庆",
    "黄山",
    "滁州",
    "阜阳",
    "宿州",
    "六安",
    "亳州",
    "池州",
    "宣城",
    "山东",
    "济南",
    "青岛",
    "淄博",
    "枣庄",
    "东营",
    "烟台",
    "潍坊",
    "济宁",
    "泰安",
    "威海",
    "日照",
    "临沂",
    "德州",
    "聊城",
    "滨州",
    "菏泽",
]

PRODUCTION_DEBUG_KEYWORDS = sorted(
    set(
        INDUSTRY_DEBUG_KEYWORDS
        + [
            "生产基地",
            "新建",
            "新建项目",
            "扩建",
            "扩建项目",
            "改建",
            "改建项目",
            "包装车间",
            "新增产能",
        ]
    )
)

DEBUG_COLUMNS = [
    "标题",
    "链接",
    "来源",
    "发布日期",
    "搜索关键词",
    "原始文本",
    "省份",
    "城市",
]


def run_eia_debug():
    raw_df = load_raw_data()
    raw_df = ensure_debug_columns(raw_df)
    raw_df.to_excel(DEBUG_FILE, index=False, engine="openpyxl")

    stats = build_stats(raw_df)
    eia_counts = count_keywords(raw_df, EIA_DEBUG_KEYWORDS)
    industry_counts = count_keywords(raw_df, INDUSTRY_DEBUG_KEYWORDS)
    region_counts = count_keywords(raw_df, REGION_DEBUG_KEYWORDS)
    sample_titles = build_samples(raw_df, limit=100)

    lines = build_diagnosis_lines(
        stats,
        eia_counts,
        industry_counts,
        region_counts,
        sample_titles,
    )

    with open(DIAGNOSIS_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print_summary(stats, eia_counts, industry_counts, region_counts, sample_titles)
    print(f"[DONE] Debug file: {DEBUG_FILE}")
    print(f"[DONE] Diagnosis: {DIAGNOSIS_FILE}")

    return {
        "stats": stats,
        "eia_counts": eia_counts,
        "industry_counts": industry_counts,
        "region_counts": region_counts,
        "sample_titles": sample_titles,
    }


def load_raw_data():
    if os.path.exists(RAW_FILE):
        return pd.read_excel(RAW_FILE)

    session = eia_monitor.create_session()
    raw_items = []

    for source in EIA_SOURCES:
        if not source.get("enabled", False):
            continue

        raw_items.extend(eia_monitor.fetch_source_items(source, session))
        time.sleep(1)

    return raw_items_to_df(raw_items)


def raw_items_to_df(raw_items):
    rows = []

    for item in raw_items:
        source = item.get("source", {}) or {}
        title = clean_cell(item.get("title", ""))
        text = clean_cell(item.get("text", ""))
        query = clean_cell(item.get("query", ""))
        combined_text = " ".join([title, text, query])

        rows.append(
            {
                "标题": title,
                "链接": clean_cell(item.get("link", "")),
                "来源": clean_cell(source.get("name", "")),
                "发布日期": eia_monitor.detect_notice_date(combined_text),
                "搜索关键词": query,
                "原始文本": text,
                "省份": eia_monitor.detect_province(combined_text, source),
                "城市": eia_monitor.detect_city(combined_text),
            }
        )

    return pd.DataFrame(rows)


def ensure_debug_columns(df):
    for column in DEBUG_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    extra_columns = [
        column
        for column in df.columns
        if column not in DEBUG_COLUMNS
    ]
    return df[DEBUG_COLUMNS + extra_columns]


def build_stats(df):
    text_series = build_text_series(df)
    eia_mask = text_series.apply(lambda text: contains_any(text, EIA_DEBUG_KEYWORDS))
    industry_mask = text_series.apply(lambda text: contains_any(text, PRODUCTION_DEBUG_KEYWORDS))
    region_mask = text_series.apply(lambda text: contains_any(text, REGION_DEBUG_KEYWORDS))
    title_series = df["标题"].fillna("").astype(str).str.strip()

    return {
        "raw_count": len(df),
        "unique_titles": int(title_series[title_series != ""].nunique()),
        "province_matched": int(region_mask.sum()),
        "industry_matched": int(industry_mask.sum()),
        "eia_matched": int(eia_mask.sum()),
        "province_industry": int((region_mask & industry_mask).sum()),
        "eia_industry": int((eia_mask & industry_mask).sum()),
        "final_matched": int((eia_mask & industry_mask & region_mask).sum()),
    }


def count_keywords(df, keywords):
    text_series = build_text_series(df)
    return {
        keyword: int(text_series.apply(lambda text: keyword in text).sum())
        for keyword in keywords
    }


def build_samples(df, limit=100):
    titles = [
        clean_cell(title)
        for title in df["标题"].fillna("").astype(str).tolist()
        if clean_cell(title)
    ]

    if titles:
        return titles[:limit]

    return [
        clean_cell(text)
        for text in df["原始文本"].fillna("").astype(str).tolist()
        if clean_cell(text)
    ][:limit]


def build_diagnosis_lines(
    stats,
    eia_counts,
    industry_counts,
    region_counts,
    sample_titles,
):
    lines = [
        "PackagingRadar EIA Debug Diagnosis",
        f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "===== SUMMARY =====",
        f"Raw count: {stats['raw_count']}",
        f"Unique titles: {stats['unique_titles']}",
        f"Province matched: {stats['province_matched']}",
        f"Industry matched: {stats['industry_matched']}",
        f"EIA matched: {stats['eia_matched']}",
        f"Province + Industry: {stats['province_industry']}",
        f"EIA + Industry: {stats['eia_industry']}",
        f"Final matched: {stats['final_matched']}",
        "",
        "===== EIA KEYWORDS =====",
    ]
    lines.extend(format_keyword_counts(eia_counts))
    lines.append("")
    lines.append("===== INDUSTRY KEYWORDS =====")
    lines.extend(format_keyword_counts(industry_counts))
    lines.append("")
    lines.append("===== REGION KEYWORDS =====")
    lines.extend(format_keyword_counts(region_counts))
    lines.append("")
    lines.append("===== CROSS STATS =====")
    lines.append(f"EIA + Industry: {stats['eia_industry']}")
    lines.append(f"Industry + Region: {stats['province_industry']}")
    lines.append(f"EIA + Industry + Region: {stats['final_matched']}")
    lines.append("")
    lines.append("===== SAMPLE TITLES =====")
    lines.extend(sample_titles)
    return lines


def print_summary(stats, eia_counts, industry_counts, region_counts, sample_titles):
    print(f"[DONE] Raw count: {stats['raw_count']}")
    print(f"[DONE] Unique titles: {stats['unique_titles']}")
    print(f"[DONE] Province matched: {stats['province_matched']}")
    print(f"[DONE] Industry matched: {stats['industry_matched']}")
    print(f"[DONE] EIA matched: {stats['eia_matched']}")
    print(f"[DONE] Province + Industry: {stats['province_industry']}")
    print(f"[DONE] EIA + Industry: {stats['eia_industry']}")
    print(f"[DONE] Final matched: {stats['final_matched']}")
    print("")
    print("===== EIA KEYWORDS =====")
    print_lines(format_keyword_counts(eia_counts))
    print("")
    print("===== INDUSTRY KEYWORDS =====")
    print_lines(format_keyword_counts(industry_counts))
    print("")
    print("===== REGION KEYWORDS =====")
    print_lines(format_keyword_counts(region_counts))
    print("")
    print("===== CROSS STATS =====")
    print(f"EIA + Industry : {stats['eia_industry']}")
    print(f"Industry + Region : {stats['province_industry']}")
    print(f"EIA + Industry + Region : {stats['final_matched']}")
    print("")
    print("===== SAMPLE TITLES =====")
    print_lines(sample_titles[:100])


def format_keyword_counts(counts):
    return [
        f"{keyword} : {count}"
        for keyword, count in counts.items()
    ]


def print_lines(lines):
    for line in lines:
        print(line)


def build_text_series(df):
    return df.apply(
        lambda row: " ".join(
            [
                clean_cell(row.get("标题", "")),
                clean_cell(row.get("原始文本", "")),
                clean_cell(row.get("省份", "")),
                clean_cell(row.get("城市", "")),
            ]
        ),
        axis=1,
    )


def contains_any(text, keywords):
    return any(keyword in clean_cell(text) for keyword in keywords)


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    run_eia_debug()
