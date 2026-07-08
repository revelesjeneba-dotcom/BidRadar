import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date
import os
import re
import time
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from expansion_keywords import EXPANSION_KEYWORDS, PRIORITY_INDUSTRIES
from expansion_sources import EXPANSION_SOURCES


OUTPUT_FILE = "expansion_projects.xlsx"

OUTPUT_COLUMNS = [
    "唯一ID",
    "采集日期",
    "企业名称",
    "项目名称",
    "行业",
    "省份",
    "城市",
    "事件类型",
    "投资金额",
    "来源",
    "链接",
    "推荐等级",
    "推荐动作",
    "跟进状态",
    "备注",
]

EVENT_SCORE_RULES = [
    ("新建生产基地", 60),
    ("生产基地", 60),
    ("扩产", 50),
    ("扩建", 50),
]

INDUSTRY_SCORE_RULES = [
    ("食品", 30),
    ("乳业", 30),
    ("酒业", 30),
    ("酒类", 30),
    ("家电", 20),
    ("电子", 20),
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


def run_expansion_monitor(
    sources=None,
    output_file=OUTPUT_FILE,
):
    if sources is None:
        sources = EXPANSION_SOURCES

    session = create_session()
    raw_items = []

    for source in sources:
        if not source.get("enabled", False):
            continue

        source_url = clean_cell(source.get("url", ""))

        if not source_url:
            continue

        raw_items.extend(fetch_source_items(source, session))
        time.sleep(1)

    records = []
    collected_date = date.today().strftime("%Y-%m-%d")

    for item in raw_items:
        record = build_project_record(item, collected_date)

        if not is_valid_expansion_project(record):
            continue

        record["唯一ID"] = make_unique_id(record)
        score = score_expansion_project(record)
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

    print(f"原始数量：{len(raw_items)}")
    print(f"有效数量：{len(current_df)}")
    print(f"新增数量：{len(new_df)}")
    print(f"导出文件：{output_file}")

    return {
        "raw_count": len(raw_items),
        "valid_count": len(current_df),
        "new_count": len(new_df),
        "output_file": output_file,
    }


def create_session():
    session = requests.Session()
    session.trust_env = False
    return session


def fetch_source_items(source, session):
    source_url = clean_cell(source.get("url", ""))
    print(f"[CHECK] {source.get('name', '')}: {source_url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        response = session.get(source_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[ERROR] Source skipped: {source.get('name', '')}; reason: {error}")
        return []

    response.encoding = response.apparent_encoding

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as error:
        print(f"[ERROR] Source parse failed: {source.get('name', '')}; reason: {error}")
        return []

    items = []
    page_text = soup.get_text(" ", strip=True)

    if contains_expansion_signal(page_text):
        items.append(
            {
                "title": clean_text(soup.title.get_text(" ", strip=True) if soup.title else source.get("name", "")),
                "text": page_text[:1200],
                "link": source_url,
                "source": source,
            }
        )

    for link_tag in soup.find_all("a", href=True):
        title = clean_text(link_tag.get_text(" ", strip=True))
        link = clean_link(link_tag.get("href", ""), source_url)

        if not title or not is_public_http_url(link):
            continue

        context_text = clean_text(link_tag.parent.get_text(" ", strip=True) if link_tag.parent else title)

        if not contains_expansion_signal(" ".join([title, context_text])):
            continue

        items.append(
            {
                "title": title,
                "text": context_text,
                "link": link,
                "source": source,
            }
        )

    print(f"[DONE] Source items: {len(items)}")
    return items


def build_project_record(item, collected_date):
    source = item["source"]
    title = clean_text(item.get("title", ""))
    text = clean_text(" ".join([title, item.get("text", "")]))
    industry = detect_industry(text)
    event_type = detect_event_type(text)

    return {
        "唯一ID": "",
        "采集日期": collected_date,
        "企业名称": detect_enterprise_name(text),
        "项目名称": title,
        "行业": industry,
        "省份": detect_province(text, source),
        "城市": detect_city(text),
        "事件类型": event_type,
        "投资金额": detect_investment_amount(text),
        "来源": clean_cell(source.get("name", "")),
        "链接": clean_cell(item.get("link", "")),
        "推荐等级": "",
        "推荐动作": "",
        "跟进状态": "待跟进",
        "备注": "扩产项目雷达自动采集",
    }


def is_valid_expansion_project(record):
    text = " ".join(
        [
            clean_cell(record.get("项目名称", "")),
            clean_cell(record.get("企业名称", "")),
            clean_cell(record.get("事件类型", "")),
            clean_cell(record.get("行业", "")),
        ]
    )
    return contains_any(text, EXPANSION_KEYWORDS) and contains_any(
        text,
        PRIORITY_INDUSTRIES,
    )


def score_expansion_project(record):
    text = " ".join(
        [
            clean_cell(record.get("项目名称", "")),
            clean_cell(record.get("企业名称", "")),
            clean_cell(record.get("事件类型", "")),
            clean_cell(record.get("行业", "")),
        ]
    )
    score = 0

    for keyword, points in EVENT_SCORE_RULES:
        if keyword in text:
            score += points
            break

    for keyword, points in INDUSTRY_SCORE_RULES:
        if keyword in text:
            score += points
            break

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


def detect_industry(text):
    for industry in PRIORITY_INDUSTRIES:
        if industry in text:
            return industry

    return ""


def detect_event_type(text):
    if "新建" in text and "生产基地" in text:
        return "新建生产基地"

    for keyword in EXPANSION_KEYWORDS:
        if keyword in text:
            return keyword

    return ""


def detect_province(text, source):
    source_province = clean_cell(source.get("province", ""))

    if source_province:
        return source_province

    for province in ["江苏", "安徽", "山东"]:
        if province in text:
            return province

    return ""


def detect_city(text):
    for city in CITY_KEYWORDS:
        if city in text:
            return city

    return ""


def detect_investment_amount(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(亿元|万元|万|亿)", text)

    if not match:
        return ""

    return match.group(0)


def detect_enterprise_name(text):
    match = re.search(
        r"([\u4e00-\u9fa5A-Za-z0-9（）()]{2,40}(?:集团|股份|科技|有限责任公司|有限公司|公司))",
        text,
    )

    if not match:
        return ""

    return match.group(1)


def contains_expansion_signal(text):
    return contains_any(text, EXPANSION_KEYWORDS)


def contains_any(text, keywords):
    text = clean_cell(text)
    return any(keyword in text for keyword in keywords)


def make_unique_id(record):
    link = clean_cell(record.get("链接", ""))

    if link:
        return f"link:{link}"

    project_name = clean_cell(record.get("项目名称", ""))
    source = clean_cell(record.get("来源", ""))
    return f"project:{project_name}|source:{source}"


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
        print(f"[ERROR] Existing expansion file read failed; recreating: {error}")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)


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
    run_expansion_monitor()
