"""
BidRadar V1.7 public web crawler.

Only collect public pages. Do not log in, bypass CAPTCHA, or work around
anti-crawling restrictions.
"""

from datetime import date
import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from sources import SEARCH_KEYWORDS, SOURCES


def create_session():
    """创建请求会话，并禁用系统/环境变量代理。"""
    session = requests.Session()
    session.trust_env = False
    return session


def fetch_public_bids(
    url,
    source_name,
    default_province="",
    session=None,
    search_keyword="",
):
    """
    从公开网页采集基础招标信息。

    返回字段尽量兼容 Excel 输出字段；抓不到的字段保留为空。
    """
    print(f"正在采集：{source_name} - {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    if session is None:
        session = create_session()

    try:
        response = session.get(
            url,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"采集失败，已跳过：{source_name}，原因：{error}")
        return []

    response.encoding = response.apparent_encoding

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as error:
        print(f"解析失败，已跳过：{source_name}，原因：{error}")
        return []

    bids = []
    today = date.today().strftime("%Y-%m-%d")

    # 通用策略：从页面中的链接提取标题和链接。
    for link_tag in soup.find_all("a"):
        title = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")

        if not title or not href:
            continue

        if len(title) < 6:
            continue

        full_link = urljoin(url, href)
        publish_date = _find_nearby_date(link_tag)

        bids.append(
            {
                "采集日期": today,
                "搜索关键词": search_keyword,
                "省份": default_province,
                "城市": "",
                "招标标题": title,
                "采购单位": "",
                "公告类型": "",
                "发布日期": publish_date,
                "截止日期": "",
                "预算金额": "",
                "信息来源": source_name,
                "链接": full_link,
                "匹配关键词": "",
                "价值等级": "",
                "跟进状态": "待跟进",
                "备注": "公开网页采集",
            }
        )

    print(f"采集完成：{source_name}，获取原始链接 {len(bids)} 条")
    return bids


def crawl_all_sources():
    """按 SOURCES 列表逐个采集，单个失败不影响其他来源。"""
    all_bids = []
    session = create_session()

    for source in SOURCES:
        url = source.get("url", "")
        source_name = source.get("source_name", "未知来源")
        default_province = source.get("province", "")
        supports_keyword_search = source.get("supports_keyword_search", False)
        search_url_template = source.get("search_url_template", "")

        if supports_keyword_search and search_url_template:

            for keyword in SEARCH_KEYWORDS:
                search_url = search_url_template.format(
                    keyword=quote(keyword)
                )
                bids = fetch_public_bids(
                    search_url,
                    source_name,
                    default_province,
                    session,
                    keyword,
                )
                all_bids.extend(bids)
                time.sleep(1)

            continue

        if not url:
            print(f"数据源缺少 URL，已跳过：{source_name}")
            continue

        bids = fetch_public_bids(url, source_name, default_province, session)
        all_bids.extend(bids)

    return all_bids


def _find_nearby_date(link_tag):
    """
    尝试从链接附近文本中提取日期。

    通用页面没有统一结构，所以这里只做简单识别。
    """
    parent_text = ""

    if link_tag.parent:
        parent_text = link_tag.parent.get_text(" ", strip=True)

    match = re.search(
        r"(20\d{2}|19\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})",
        parent_text,
    )

    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return ""
