import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date
import os
import re
import time
from urllib.parse import quote_plus, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from project_keywords import FOCUS_INDUSTRIES, FOCUS_REGIONS, PROJECT_KEYWORDS
from project_sources import PROJECT_SOURCES


OUTPUT_FILE = "production_projects.xlsx"
DEBUG_FILE = "production_raw_debug.xlsx"

OUTPUT_COLUMNS = [
    "唯一ID",
    "采集日期",
    "企业名称",
    "项目名称",
    "行业",
    "省份",
    "城市",
    "投资金额",
    "预计投产时间",
    "来源",
    "链接",
    "命中关键词",
    "价值分数",
    "推荐等级",
    "推荐动作",
    "跟进状态",
    "备注",
]

DEBUG_COLUMNS = [
    "标题",
    "链接",
    "来源",
    "搜索关键词",
    "原始文本",
    "省份",
    "城市",
    "命中项目关键词",
    "命中行业关键词",
]

CITY_KEYWORDS = [
    "南京",
    "苏州",
    "无锡",
    "常州",
    "南通",
    "扬州",
    "镇江",
    "泰州",
    "徐州",
    "盐城",
    "合肥",
    "芜湖",
    "滁州",
    "马鞍山",
    "蚌埠",
    "济南",
    "青岛",
    "烟台",
    "潍坊",
    "临沂",
    "淄博",
]


def run_project_monitor(
    sources=None,
    output_file=OUTPUT_FILE,
    debug_file=DEBUG_FILE,
):
    if sources is None:
        sources = PROJECT_SOURCES

    session = create_session()
    raw_items = []

    for source in sources:
        if not source.get("enabled", False):
            continue

        raw_items.extend(fetch_source_items(source, session))
        time.sleep(1)

    export_raw_debug(raw_items, debug_file)

    collected_date = date.today().strftime("%Y-%m-%d")
    records = []

    for item in raw_items:
        record = build_project_record(item, collected_date)

        if not is_valid_project(record):
            continue

        record["唯一ID"] = make_unique_id(record)
        score = score_project(record)
        record["价值分数"] = score
        record["推荐等级"] = build_recommend_level(score)
        record["推荐动作"] = build_recommend_action(score)
        records.append(record)

    current_df = pd.DataFrame(records)

    if not current_df.empty:
        current_df = current_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )

    history_df = read_history(output_file)

    for column in OUTPUT_COLUMNS:
        if column not in history_df.columns:
            history_df[column] = ""

    if not history_df.empty:
        history_df["唯一ID"] = history_df.apply(
            lambda row: existing_or_new_unique_id(row),
            axis=1,
        )
        history_df = history_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )

    history_ids = set(history_df["唯一ID"].fillna("").astype(str))

    if current_df.empty:
        new_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        new_df = current_df[
            ~current_df["唯一ID"].astype(str).isin(history_ids)
        ].copy()

    combined_df = pd.concat([history_df, new_df], ignore_index=True)

    for column in OUTPUT_COLUMNS:
        if column not in combined_df.columns:
            combined_df[column] = ""

    combined_df = combined_df[OUTPUT_COLUMNS]
    combined_df.to_excel(output_file, index=False, engine="openpyxl")

    print(f"[DONE] Raw count: {len(raw_items)}")
    print(f"[DONE] Valid count: {len(current_df)}")
    print(f"[DONE] New count: {len(new_df)}")
    print(f"[DONE] Export file: {output_file}")
    print(f"[DONE] Debug file: {debug_file}")

    return {
        "raw_count": len(raw_items),
        "valid_count": len(current_df),
        "new_count": len(new_df),
        "output_file": output_file,
        "debug_file": debug_file,
    }


def create_session():
    session = requests.Session()
    session.trust_env = False
    return session


def fetch_source_items(source, session):
    source_type = clean_cell(source.get("type", ""))

    if source_type == "public_search":
        return fetch_public_search_items(source, session)

    return fetch_public_page_items(source, session)


def fetch_public_search_items(source, session):
    items = []
    template = clean_cell(source.get("search_url_template", ""))

    for query in source.get("queries", []):
        query = clean_cell(query)

        if not query or not template:
            continue

        search_url = template.format(query=quote_plus(query))
        print(f"[CHECK] Search: {query}")
        items.extend(fetch_search_result_page(source, session, search_url, query))
        time.sleep(1)

    print(f"[DONE] Source items: {source.get('name', '')}; count: {len(items)}")
    return items


def fetch_search_result_page(source, session, search_url, query):
    try:
        response = session.get(search_url, headers=build_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[ERROR] Search skipped: {query}; reason: {error}")
        return []

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    items = []

    for result_item in soup.select("li.b_algo"):
        link_tag = result_item.find("a", href=True)

        if not link_tag:
            continue

        title = clean_text(link_tag.get_text(" ", strip=True))
        link = clean_link(link_tag.get("href", ""), search_url)
        context_text = clean_text(result_item.get_text(" ", strip=True))

        if not title or not is_public_http_url(link):
            continue

        items.append(
            {
                "title": title,
                "text": context_text,
                "link": link,
                "source": source,
                "query": query,
            }
        )

    return items


def fetch_public_page_items(source, session):
    source_url = clean_cell(source.get("url", ""))

    if not source_url:
        return []

    print(f"[CHECK] Page: {source.get('name', '')}")

    try:
        response = session.get(source_url, headers=build_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[ERROR] Page skipped: {source.get('name', '')}; reason: {error}")
        return []

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    items = []

    for link_tag in soup.find_all("a", href=True):
        title = clean_text(link_tag.get_text(" ", strip=True))
        link = clean_link(link_tag.get("href", ""), source_url)
        context_text = clean_text(link_tag.parent.get_text(" ", strip=True) if link_tag.parent else title)

        if not title or not is_public_http_url(link):
            continue

        items.append(
            {
                "title": title,
                "text": context_text,
                "link": link,
                "source": source,
                "query": "",
            }
        )

    print(f"[DONE] Page items: {len(items)}")
    return items


def export_raw_debug(raw_items, debug_file):
    rows = []

    for item in raw_items:
        source = item.get("source", {}) or {}
        title = clean_text(item.get("title", ""))
        text = clean_text(item.get("text", ""))
        content_text = build_item_text(item, include_query=False)

        rows.append(
            {
                "标题": title,
                "链接": clean_cell(item.get("link", "")),
                "来源": clean_cell(source.get("name", "")),
                "搜索关键词": clean_cell(item.get("query", "")),
                "原始文本": text,
                "省份": detect_province(content_text, source),
                "城市": detect_city(content_text),
                "命中项目关键词": "、".join(find_keywords(content_text, PROJECT_KEYWORDS)),
                "命中行业关键词": "、".join(find_keywords(content_text, FOCUS_INDUSTRIES)),
            }
        )

    debug_df = pd.DataFrame(rows)

    for column in DEBUG_COLUMNS:
        if column not in debug_df.columns:
            debug_df[column] = ""

    debug_df = debug_df[DEBUG_COLUMNS]
    debug_df.to_excel(debug_file, index=False, engine="openpyxl")
    return debug_file


def build_project_record(item, collected_date):
    source = item.get("source", {}) or {}
    title = clean_text(item.get("title", ""))
    content_text = build_item_text(item, include_query=False)
    matched_keywords = find_keywords(content_text, PROJECT_KEYWORDS + FOCUS_INDUSTRIES)

    return {
        "唯一ID": "",
        "采集日期": collected_date,
        "企业名称": detect_enterprise_name(content_text),
        "项目名称": title,
        "行业": detect_industry(content_text),
        "省份": detect_province(content_text, source),
        "城市": detect_city(content_text),
        "投资金额": detect_investment_amount(content_text),
        "预计投产时间": detect_production_time(content_text),
        "来源": clean_cell(source.get("name", "")),
        "链接": clean_cell(item.get("link", "")),
        "命中关键词": "、".join(matched_keywords),
        "价值分数": "",
        "推荐等级": "",
        "推荐动作": "",
        "跟进状态": "待跟进",
        "备注": "生产项目监控器自动采集",
    }


def is_valid_project(record):
    text = build_record_text(record)
    return contains_any(text, PROJECT_KEYWORDS) and contains_any(
        text,
        FOCUS_INDUSTRIES,
    )


def score_project(record):
    text = build_record_text(record)
    score = 0

    if "新建生产基地" in text:
        score += 60

    if "年产" in text:
        score += 40

    if "扩建项目" in text:
        score += 50

    if "新增产能" in text:
        score += 50

    if contains_any(text, ["食品", "饮料", "乳业", "酒业"]):
        score += 30
    elif contains_any(text, ["家电", "电子", "医疗", "医药"]):
        score += 20
    elif contains_any(text, ["包装", "物流"]):
        score += 20

    return score


def build_recommend_level(score):
    if score >= 90:
        return "五星"

    if score >= 70:
        return "四星"

    if score >= 50:
        return "三星"

    return "观察"


def build_recommend_action(score):
    if score >= 90:
        return "建议立即开发"

    if score >= 70:
        return "建议优先跟进"

    if score >= 50:
        return "纳入线索池"

    return "观察"


def find_keywords(text, keywords):
    return [
        keyword
        for keyword in keywords
        if keyword in text
    ]


def detect_industry(text):
    for industry in FOCUS_INDUSTRIES:
        if industry in text:
            return industry

    return ""


def detect_province(text, source):
    source_province = clean_cell(source.get("province", ""))

    if source_province:
        return source_province

    for province in FOCUS_REGIONS:
        if province in text:
            return province

    return ""


def detect_city(text):
    for city in CITY_KEYWORDS:
        if city in text:
            return city

    return ""


def detect_investment_amount(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(亿元|万元|亿|万)", text)

    if not match:
        return ""

    return match.group(0)


def detect_production_time(text):
    match = re.search(r"(预计|计划)?(20\d{2})年?(?:([0-1]?\d)月?)?(投产|建成|竣工|达产)", text)

    if not match:
        return ""

    year = match.group(2)
    month = match.group(3)

    if month:
        return f"{year}-{int(month):02d}"

    return year


def detect_enterprise_name(text):
    match = re.search(
        r"([\u4e00-\u9fa5A-Za-z0-9（）()]{2,45}(?:集团|股份|科技|有限责任公司|有限公司|公司))",
        text,
    )

    if not match:
        return ""

    return match.group(1)


def make_unique_id(record):
    link = clean_cell(record.get("链接", ""))

    if link:
        return f"link:{link}"

    project_name = clean_cell(record.get("项目名称", ""))
    enterprise_name = clean_cell(record.get("企业名称", ""))
    return f"project:{project_name}|enterprise:{enterprise_name}"


def existing_or_new_unique_id(row):
    unique_id = clean_cell(row.get("唯一ID", ""))

    if unique_id:
        return unique_id

    return make_unique_id(row.to_dict())


def read_history(output_file):
    if not os.path.exists(output_file):
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    try:
        return pd.read_excel(output_file)
    except Exception as error:
        print(f"[ERROR] Existing production file read failed; recreating: {error}")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)


def build_item_text(item, include_query=False):
    parts = [
        clean_cell(item.get("title", "")),
        clean_cell(item.get("text", "")),
    ]

    if include_query:
        parts.append(clean_cell(item.get("query", "")))

    return " ".join(parts)


def build_record_text(record):
    return " ".join(
        [
            clean_cell(record.get("企业名称", "")),
            clean_cell(record.get("项目名称", "")),
            clean_cell(record.get("行业", "")),
            clean_cell(record.get("省份", "")),
            clean_cell(record.get("城市", "")),
            clean_cell(record.get("投资金额", "")),
            clean_cell(record.get("预计投产时间", "")),
            clean_cell(record.get("命中关键词", "")),
        ]
    )


def contains_any(text, keywords):
    text = clean_cell(text)
    return any(keyword in text for keyword in keywords)


def build_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }


def clean_link(link, base_url):
    return urljoin(base_url, clean_cell(link))


def is_public_http_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)


def clean_text(value):
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    run_project_monitor()
