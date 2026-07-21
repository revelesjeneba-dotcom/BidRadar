"""
BidRadar V2.1 procurement entry source discovery.

Uses public search result pages to find candidate enterprise procurement
entrances. It does not log in, bypass CAPTCHA, or work around anti-crawling
protections.
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import datetime
import os
import time
from urllib.parse import quote_plus, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from enterprise_sources import ENTERPRISE_SOURCES
from paths import ENTERPRISE_CANDIDATES_FILE
from utils.excel_helper import read_excel_safe, write_excel_safe


OUTPUT_FILE = ENTERPRISE_CANDIDATES_FILE

SEARCH_SUFFIXES = [
    "招标",
    "采购平台",
    "SRM",
    "供应商平台",
    "电子采购",
    "招标采购",
]

CANDIDATE_COLUMNS = [
    "企业名称",
    "搜索关键词",
    "候选网址",
    "网页标题",
    "来源",
    "是否确认",
    "备注",
]

DEFAULT_CONFIRM_STATUS = "否"
DEFAULT_REMARK = "待人工确认"


def create_session():
    """Create a requests session without environment proxy inheritance."""
    session = requests.Session()
    session.trust_env = False
    return session


def build_search_keywords(enterprise_name):
    return [
        f"{enterprise_name} {suffix}"
        for suffix in SEARCH_SUFFIXES
    ]


def discover_enterprise_candidates(output_file=OUTPUT_FILE):
    """Discover candidate procurement URLs and export a deduplicated Excel."""
    session = create_session()
    candidates = []

    for source in ENTERPRISE_SOURCES:
        enterprise_name = source.get("name", "").strip()

        if not enterprise_name:
            continue

        for keyword in build_search_keywords(enterprise_name):
            results = search_public_web(keyword, session=session)

            for result in results:
                candidates.append(
                    {
                        "企业名称": enterprise_name,
                        "搜索关键词": keyword,
                        "候选网址": result["url"],
                        "网页标题": result["title"],
                        "来源": result["source"],
                        "是否确认": DEFAULT_CONFIRM_STATUS,
                        "备注": DEFAULT_REMARK,
                    }
                )

            time.sleep(1)

    export_candidates(candidates, output_file)
    return candidates


def search_public_web(keyword, session=None):
    """
    Search public webpages for one keyword.

    The implementation uses Bing's public search result page. If the page is
    unavailable, blocked, or changes structure, the keyword is skipped.
    """
    if session is None:
        session = create_session()

    search_url = f"https://www.bing.com/search?q={quote_plus(keyword)}"
    print(f"[CHECK] Searching: {keyword}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        response = session.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[ERROR] Search skipped: {keyword}; reason: {error}")
        return []

    response.encoding = response.apparent_encoding

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as error:
        print(f"[ERROR] Search result parsing skipped: {keyword}; reason: {error}")
        return []

    results = []

    for result_item in soup.select("li.b_algo"):
        link_tag = result_item.find("a", href=True)

        if not link_tag:
            continue

        title = link_tag.get_text(" ", strip=True)
        url = link_tag.get("href", "").strip()

        if not title or not url:
            continue

        if not _is_public_http_url(url):
            continue

        results.append(
            {
                "url": url,
                "title": title,
                "source": "Bing公开搜索",
            }
        )

    print(f"[DONE] Search complete: {keyword}; candidates: {len(results)}")
    return results


def export_candidates(candidates, output_file=OUTPUT_FILE):
    """Merge with existing Excel and deduplicate every run."""
    current_df = pd.DataFrame(candidates)

    for column in CANDIDATE_COLUMNS:
        if column not in current_df.columns:
            current_df[column] = ""

    current_df = current_df[CANDIDATE_COLUMNS]
    history_df = _read_history(output_file)

    combined_df = pd.concat([history_df, current_df], ignore_index=True)

    for column in CANDIDATE_COLUMNS:
        if column not in combined_df.columns:
            combined_df[column] = ""

    combined_df["候选网址"] = combined_df["候选网址"].astype(str).str.strip()
    combined_df = combined_df[combined_df["候选网址"] != ""]
    combined_df = combined_df.drop_duplicates(
        subset=["企业名称", "搜索关键词", "候选网址"],
        keep="first",
    )
    combined_df = combined_df[CANDIDATE_COLUMNS]
    write_excel_safe(
        combined_df,
        output_file,
        required_columns=CANDIDATE_COLUMNS,
    )

    print(f"[DONE] Candidate file: {output_file}")
    print(f"[DONE] Candidate count: {len(combined_df)}")
    return output_file


def _read_history(output_file):
    if not os.path.exists(output_file):
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)

    history_df = read_excel_safe(output_file)

    for column in CANDIDATE_COLUMNS:
        if column not in history_df.columns:
            history_df[column] = ""

    return history_df[CANDIDATE_COLUMNS]


def _is_public_http_url(url):
    parsed = urlparse(url)

    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)


if __name__ == "__main__":
    discover_enterprise_candidates()
