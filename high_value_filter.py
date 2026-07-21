import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import os

import pandas as pd

from paths import BID_RESULTS, HIGH_VALUE_LEADS


HIGH_VALUE_OUTPUT_FILE = HIGH_VALUE_LEADS

HIGH_VALUE_KEYWORDS = [
    "供应商征集",
    "供应商招募",
    "供应商入围",
    "年度采购",
    "框架协议",
    "战略采购",
]

PRIORITY_INDUSTRIES = [
    "食品",
    "乳业",
    "酒业",
    "家电",
    "电子",
    "物流",
    "新能源",
]

PRIORITY_BUYER_WORDS = [
    "集团",
    "股份",
    "科技",
    "有限公司",
]

OUTPUT_COLUMNS = [
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


def export_high_value_leads(
    input_file=BID_RESULTS,
    output_file=HIGH_VALUE_OUTPUT_FILE,
):
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file not found: {input_file}")
        return {
            "total": 0,
            "high_value": 0,
            "five_star": 0,
            "immediate": 0,
            "output_file": output_file,
        }

    df = pd.read_excel(input_file)
    total_count = len(df)
    df = ensure_columns(df)
    high_value_df = filter_high_value(df).copy()

    if not high_value_df.empty:
        high_value_df["推荐等级"] = high_value_df.apply(
            lambda row: build_recommend_level(row),
            axis=1,
        )
        high_value_df["推荐动作"] = high_value_df.apply(
            lambda row: build_recommend_action(row),
            axis=1,
        )
        high_value_df["_排序分"] = high_value_df.apply(
            lambda row: build_sort_score(row),
            axis=1,
        )
        high_value_df = high_value_df.sort_values(
            by=["_排序分", "价值分数"],
            ascending=[False, False],
        )

    output_df = high_value_df[OUTPUT_COLUMNS] if not high_value_df.empty else pd.DataFrame(columns=OUTPUT_COLUMNS)
    output_df.to_excel(output_file, index=False, engine="openpyxl")

    five_star_count = len(
        output_df[output_df["推荐等级"].astype(str) == "五星线索"]
    )
    immediate_count = len(
        output_df[output_df["推荐动作"].astype(str) == "建议立即开发"]
    )

    print(f"总记录数：{total_count}")
    print(f"高价值线索数：{len(output_df)}")
    print(f"五星线索数：{five_star_count}")
    print(f"建议立即开发数量：{immediate_count}")
    print(f"导出文件：{output_file}")

    return {
        "total": total_count,
        "high_value": len(output_df),
        "five_star": five_star_count,
        "immediate": immediate_count,
        "output_file": output_file,
    }


def ensure_columns(df):
    required_columns = [
        "招标标题",
        "采购单位",
        "省份",
        "城市",
        "价值分数",
        "价值等级",
        "推荐跟进",
        "跟进优先级",
        "链接",
        "公告类型",
        "备注",
        "匹配关键词",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    return df


def filter_high_value(df):
    return df[
        df.apply(
            lambda row: contains_any(build_match_text(row), HIGH_VALUE_KEYWORDS),
            axis=1,
        )
    ]


def build_recommend_level(row):
    score = parse_score(row.get("价值分数", 0))

    if score >= 90:
        return "五星线索"

    if score >= 70:
        return "四星线索"

    if has_priority_industry(row) and has_priority_buyer(row):
        return "四星线索"

    if has_priority_industry(row) or has_priority_buyer(row):
        return "三星线索"

    return "重点线索"


def build_recommend_action(row):
    score = parse_score(row.get("价值分数", 0))
    level = build_recommend_level(row)

    if score >= 70 or level in ["五星线索", "四星线索"]:
        return "建议立即开发"

    if has_priority_industry(row) or has_priority_buyer(row):
        return "建议优先跟进"

    return "建议纳入线索池"


def build_sort_score(row):
    score = parse_score(row.get("价值分数", 0))

    if has_priority_industry(row):
        score += 20

    if has_priority_buyer(row):
        score += 20

    return score


def build_match_text(row):
    return " ".join(
        [
            clean_cell(row.get("招标标题", "")),
            clean_cell(row.get("采购单位", "")),
            clean_cell(row.get("公告类型", "")),
            clean_cell(row.get("备注", "")),
            clean_cell(row.get("匹配关键词", "")),
        ]
    )


def has_priority_industry(row):
    return contains_any(build_match_text(row), PRIORITY_INDUSTRIES)


def has_priority_buyer(row):
    return contains_any(
        clean_cell(row.get("采购单位", "")),
        PRIORITY_BUYER_WORDS,
    )


def contains_any(text, keywords):
    text = clean_cell(text)
    return any(keyword in text for keyword in keywords)


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
    export_high_value_leads()
