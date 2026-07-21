import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import os
import re
import time
from urllib.parse import quote_plus, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from paths import CUSTOMER_CONTACT_CANDIDATES_FILE, CUSTOMER_POOL_FILE
from utils.excel_helper import read_excel_safe, write_excel_safe


OUTPUT_FILE = CUSTOMER_CONTACT_CANDIDATES_FILE

CUSTOMER_COLUMNS = [
    "企业名称",
    "官网",
    "电话",
    "邮箱",
    "采购平台网址",
]

CANDIDATE_COLUMNS = [
    "企业名称",
    "搜索关键词",
    "候选标题",
    "候选网址",
    "候选电话",
    "候选邮箱",
    "来源",
    "是否确认",
    "备注",
]

SEARCH_SUFFIXES = [
    "官网",
    "联系电话",
    "采购平台",
    "供应商平台",
]

DEFAULT_CONFIRM_STATUS = "否"
DEFAULT_REMARK = "待人工确认"

PHONE_PATTERN = re.compile(
    r"(?:(?:\+?86[-\s]?)?1[3-9]\d{9}|0\d{2,3}[-\s]?\d{7,8})"
)
EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def find_contact_candidates(
    customer_pool_file=CUSTOMER_POOL_FILE,
    output_file=OUTPUT_FILE,
):
    customers_df = read_customers(customer_pool_file)
    target_df = filter_customers_needing_contact(customers_df)
    session = create_session()
    candidates = []

    for _, customer in target_df.iterrows():
        company_name = clean_cell(customer.get("企业名称", ""))

        if not company_name:
            continue

        for keyword in build_search_keywords(company_name):
            results = search_public_web(keyword, session=session)

            for result in results:
                candidates.append(
                    {
                        "企业名称": company_name,
                        "搜索关键词": keyword,
                        "候选标题": result["title"],
                        "候选网址": result["url"],
                        "候选电话": result["phone"],
                        "候选邮箱": result["email"],
                        "来源": result["source"],
                        "是否确认": DEFAULT_CONFIRM_STATUS,
                        "备注": DEFAULT_REMARK,
                    }
                )

            time.sleep(1)

    candidates_df = pd.DataFrame(candidates)

    for column in CANDIDATE_COLUMNS:
        if column not in candidates_df.columns:
            candidates_df[column] = ""

    if not candidates_df.empty:
        candidates_df = candidates_df.drop_duplicates(
            subset=["企业名称", "搜索关键词", "候选网址"],
            keep="first",
        )

    candidates_df = candidates_df[CANDIDATE_COLUMNS]
    write_excel_safe(
        candidates_df,
        output_file,
        required_columns=CANDIDATE_COLUMNS,
    )

    print(f"客户数量：{len(target_df)}")
    print(f"候选结果数量：{len(candidates_df)}")
    print(f"导出文件：{output_file}")

    return {
        "customers": len(target_df),
        "candidates": len(candidates_df),
        "output_file": output_file,
    }


def read_customers(customer_pool_file):
    if not os.path.exists(customer_pool_file):
        print(f"[ERROR] Customer pool file not found: {customer_pool_file}")
        return pd.DataFrame(columns=CUSTOMER_COLUMNS)

    df = read_excel_safe(customer_pool_file)

    for column in CUSTOMER_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df


def filter_customers_needing_contact(df):
    if df.empty:
        return df

    mask = (
        df["官网"].apply(is_empty)
        | df["电话"].apply(is_empty)
        | df["邮箱"].apply(is_empty)
        | df["采购平台网址"].apply(is_empty)
    )
    return df[mask].copy()


def build_search_keywords(company_name):
    return [
        f"{company_name} {suffix}"
        for suffix in SEARCH_SUFFIXES
    ]


def create_session():
    session = requests.Session()
    session.trust_env = False
    return session


def search_public_web(keyword, session):
    search_url = f"https://www.bing.com/search?q={quote_plus(keyword)}"
    print(f"[CHECK] Search: {keyword}")

    try:
        response = session.get(
            search_url,
            headers=build_headers(),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[ERROR] Search skipped: {keyword}; reason: {error}")
        return []

    response.encoding = response.apparent_encoding

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as error:
        print(f"[ERROR] Search result parse skipped: {keyword}; reason: {error}")
        return []

    results = []

    for result_item in soup.select("li.b_algo"):
        link_tag = result_item.find("a", href=True)

        if not link_tag:
            continue

        title = clean_cell(link_tag.get_text(" ", strip=True))
        url = clean_cell(link_tag.get("href", ""))
        text = clean_cell(result_item.get_text(" ", strip=True))

        if not title or not url or not is_public_http_url(url):
            continue

        results.append(
            {
                "title": title,
                "url": url,
                "phone": extract_first(PHONE_PATTERN, text),
                "email": extract_first(EMAIL_PATTERN, text),
                "source": "Bing公开搜索",
            }
        )

    print(f"[DONE] Search results: {keyword}; count: {len(results)}")
    return results


def extract_first(pattern, text):
    match = pattern.search(clean_cell(text))

    if not match:
        return ""

    return match.group(0)


def build_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }


def is_public_http_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)


def is_empty(value):
    return clean_cell(value) == ""


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


if __name__ == "__main__":
    find_contact_candidates()
