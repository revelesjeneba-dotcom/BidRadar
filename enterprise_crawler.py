"""
BidRadar V2.0 enterprise procurement platform crawler.

Only reads public procurement pages. It does not log in, bypass CAPTCHA, or
work around anti-crawling protections.
"""

from datetime import date
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from enterprise_sources import ENTERPRISE_SOURCES


def create_session():
    """Create a requests session without environment proxy inheritance."""
    session = requests.Session()
    session.trust_env = False
    return session


def crawl_enterprise_sources(sources=None):
    """Collect public links from enabled enterprise procurement platforms."""
    all_bids = []
    session = create_session()

    if sources is None:
        sources = ENTERPRISE_SOURCES

    for source in sources:
        if not source.get("enabled", True):
            print(f"企业采购源已禁用，跳过：{source.get('name', '未知企业')}")
            continue

        procurement_url = str(source.get("procurement_url", "")).strip()
        enterprise_name = source.get("name", "未知企业")

        if not procurement_url:
            print(f"企业采购源缺少 procurement_url，已跳过：{enterprise_name}")
            continue

        bids = fetch_enterprise_bids(source, session)
        all_bids.extend(bids)

    return all_bids


def fetch_enterprise_bids(source, session=None):
    """
    Fetch one public enterprise procurement page.

    Returned records use the same field names as bid_results.xlsx.
    """
    enterprise_name = source.get("name", "未知企业")
    procurement_url = str(source.get("procurement_url", "")).strip()
    province = source.get("province", "")
    keywords = source.get("keywords", [])

    print(f"正在采集企业采购平台：{enterprise_name} - {procurement_url}")

    if session is None:
        session = create_session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        response = session.get(
            procurement_url,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"企业采购平台访问失败，已跳过：{enterprise_name}，原因：{error}")
        return []

    response.encoding = response.apparent_encoding

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as error:
        print(f"企业采购平台解析失败，已跳过：{enterprise_name}，原因：{error}")
        return []

    bids = []
    collected_date = date.today().strftime("%Y-%m-%d")

    for link_tag in soup.find_all("a"):
        title = link_tag.get_text(" ", strip=True)
        href = link_tag.get("href", "")

        if not title or not href:
            continue

        if len(title) < 6:
            continue

        full_link = urljoin(procurement_url, href)
        nearby_text = _get_nearby_text(link_tag)
        publish_date = _find_nearby_date(nearby_text)
        matched_keywords = _find_matched_keywords(
            f"{title} {nearby_text}",
            keywords,
        )

        bids.append(
            {
                "采集日期": collected_date,
                "搜索关键词": "、".join(matched_keywords),
                "省份": province,
                "城市": "",
                "招标标题": title,
                "采购单位": enterprise_name,
                "公告类型": "",
                "发布日期": publish_date,
                "截止日期": "",
                "预算金额": "",
                "信息来源": f"{enterprise_name}企业采购平台",
                "链接": full_link,
                "匹配关键词": "、".join(matched_keywords),
                "价值等级": "",
                "跟进状态": "待跟进",
                "备注": "大型企业采购平台公开网页采集",
            }
        )

    print(f"企业采购平台采集完成：{enterprise_name}，获取原始链接 {len(bids)} 条")
    return bids


def _get_nearby_text(link_tag):
    if link_tag.parent:
        return link_tag.parent.get_text(" ", strip=True)

    return link_tag.get_text(" ", strip=True)


def _find_nearby_date(text):
    match = re.search(
        r"(20\d{2}|19\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})",
        text,
    )

    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return ""


def _find_matched_keywords(text, keywords):
    return [
        keyword
        for keyword in keywords
        if keyword and keyword in text
    ]


if __name__ == "__main__":
    results = crawl_enterprise_sources()
    print(f"企业采购平台原始数据数量：{len(results)}")
