"""
BidRadar V2.2 candidate procurement entry ranker.

Reads enterprise_candidates.xlsx, scores candidate URLs, and writes the score
columns back to the same Excel file.
"""

import os
from urllib.parse import urlparse

import pandas as pd

from enterprise_sources import ENTERPRISE_SOURCES
from utils.excel_helper import read_excel_safe, write_excel_safe


INPUT_FILE = "enterprise_candidates.xlsx"

URL_SCORE_KEYWORDS = [
    "srm",
    "supplier",
    "procurement",
    "purchase",
    "tender",
    "bidding",
    "portal",
    "ec",
]

TITLE_SCORE_KEYWORDS = [
    "供应商",
    "采购",
    "招标",
    "采购平台",
    "电子采购",
    "SRM",
]

NEGATIVE_KEYWORDS = [
    "zhihu",
    "baidu",
    "weibo",
    "toutiao",
    "tianyancha",
    "qcc",
    "招聘",
    "新闻",
    "百科",
]

RANK_COLUMNS = [
    "候选评分",
    "推荐等级",
    "建议",
]


def rank_candidates(input_file=INPUT_FILE):
    """Score enterprise candidate URLs and update enterprise_candidates.xlsx."""
    if not os.path.exists(input_file):
        print(f"候选入口文件不存在：{input_file}")
        return input_file

    df = read_excel_safe(input_file)
    homepage_domains = build_homepage_domain_map()

    for column in ["企业名称", "候选网址", "网页标题"]:
        if column not in df.columns:
            df[column] = ""

    scores = []
    levels = []
    suggestions = []

    for _, row in df.iterrows():
        score = score_candidate(row, homepage_domains)
        level = get_recommendation_level(score)
        suggestion = get_suggestion(level)

        scores.append(score)
        levels.append(level)
        suggestions.append(suggestion)

    df["候选评分"] = scores
    df["推荐等级"] = levels
    df["建议"] = suggestions

    write_excel_safe(
        df,
        input_file,
        required_columns=RANK_COLUMNS,
    )
    print(f"已更新候选入口评分：{input_file}")
    print(f"候选入口数量：{len(df)}")
    return input_file


def score_candidate(row, homepage_domains):
    enterprise_name = str(row.get("企业名称", "")).strip()
    url = str(row.get("候选网址", "")).strip()
    title = str(row.get("网页标题", "")).strip()
    url_lower = url.lower()
    title_lower = title.lower()
    score = 0

    for keyword in URL_SCORE_KEYWORDS:
        if keyword in url_lower:
            score += 30

    for keyword in TITLE_SCORE_KEYWORDS:
        if keyword.lower() in title_lower:
            score += 20

    if is_enterprise_domain(url, homepage_domains.get(enterprise_name, "")):
        score += 30

    negative_text = f"{url_lower} {title_lower}"

    for keyword in NEGATIVE_KEYWORDS:
        if keyword.lower() in negative_text:
            score -= 100

    return score


def build_homepage_domain_map():
    domains = {}

    for source in ENTERPRISE_SOURCES:
        name = source.get("name", "")
        homepage = source.get("homepage", "")
        domains[name] = normalize_domain(homepage)

    return domains


def normalize_domain(url):
    parsed = urlparse(str(url).strip())
    domain = parsed.netloc or parsed.path
    domain = domain.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def is_enterprise_domain(candidate_url, homepage_domain):
    if not homepage_domain:
        return False

    candidate_domain = normalize_domain(candidate_url)

    return (
        candidate_domain == homepage_domain
        or candidate_domain.endswith(f".{homepage_domain}")
    )


def get_recommendation_level(score):
    if score >= 90:
        return "★★★★★"

    if score >= 70:
        return "★★★★"

    if score >= 50:
        return "★★★"

    if score >= 30:
        return "★★"

    return "★"


def get_suggestion(level):
    if level in ["★★★★★", "★★★★"]:
        return "建议人工确认"

    if level == "★★★":
        return "可选"

    return "忽略"


if __name__ == "__main__":
    rank_candidates()
