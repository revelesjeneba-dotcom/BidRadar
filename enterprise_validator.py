"""
BidRadar V2.3 enterprise procurement entry validator.

Validates procurement_url entries from enterprise_url_status.xlsx using normal
public HTTP requests. It does not log in, bypass CAPTCHA, or work around
anti-crawling protections.
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import datetime
import hashlib
import os
from pathlib import Path
import time
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from paths import ENTERPRISE_URL_STATUS_FILE
from utils.excel_helper import read_excel_safe, write_excel_safe


STATUS_FILE = ENTERPRISE_URL_STATUS_FILE

VALIDATION_COLUMNS = [
    "页面标题",
    "HTTP状态码",
    "是否跳转",
    "访问状态",
    "平台类型",
    "是否公开",
    "需要登录",
    "支持搜索",
    "是否可采集",
    "验证结果",
    "最后检查时间",
]

LOGIN_KEYWORDS = [
    "账号",
    "密码",
    "登录",
    "验证码",
    "用户名",
    "用户登录",
    "账号登录",
    "密码登录",
    "忘记密码",
    "登录方式",
    "登陆",
    "login",
    "sign in",
]

LOGIN_KEYWORD_THRESHOLD = 2

PUBLIC_NOTICE_KEYWORDS = [
    "公告",
    "招标公告",
    "采购公告",
    "中标",
    "成交",
    "公示",
    "招标采购",
]

SUPPLIER_PORTAL_KEYWORDS = [
    "供应商",
    "supplier",
    "srm",
    "供应商门户",
    "供应商平台",
]

PROCUREMENT_APP_KEYWORDS = [
    "采购协同平台",
    "采购平台",
    "供应商平台",
    "供应商门户",
    "srm",
]

JAVASCRIPT_APP_KEYWORDS = [
    "doesn't work properly without javascript",
    "please enable it to continue",
    "请启用javascript",
    "请启用 javascript",
]

SEARCH_KEYWORDS = [
    "搜索",
    "查询",
    "检索",
    "search",
]


class EnterpriseStatusChangedError(RuntimeError):
    """Raised when the status workbook changes during validation."""


def validate_enterprise_urls(status_file=STATUS_FILE):
    """Validate procurement platform URLs and save results to Excel."""
    if not os.path.exists(status_file):
        print(f"[ERROR] Status file not found: {status_file}")
        return status_file

    original_fingerprint = _file_fingerprint(status_file)
    df = read_excel_safe(status_file)
    _assert_file_unchanged(status_file, original_fingerprint)

    for column in VALIDATION_COLUMNS:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].astype("object")

    stats = {
        "total": len(df),
        "public_platform": 0,
        "login_platform": 0,
        "unavailable": 0,
        "collectable": 0,
    }

    session = create_session()

    for index, row in df.iterrows():
        url = clean_cell(row.get("采购平台网址", ""))
        checked_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not url:
            result = build_empty_url_result(checked_time)
        else:
            result = validate_url(url, session, checked_time)
            time.sleep(1)

        for column, value in result.items():
            df.at[index, column] = value

        platform_type = result["平台类型"]

        if platform_type == "公开公告平台":
            stats["public_platform"] += 1

        if platform_type == "登录采购平台":
            stats["login_platform"] += 1

        if platform_type == "不可访问":
            stats["unavailable"] += 1

        if result["是否可采集"] == "是":
            stats["collectable"] += 1

    _assert_file_unchanged(status_file, original_fingerprint)
    write_excel_safe(
        df,
        status_file,
        required_columns=VALIDATION_COLUMNS,
    )
    print_validation_stats(stats)
    return status_file


def create_session():
    session = requests.Session()
    session.trust_env = False
    return session


def validate_url(url, session, checked_time):
    print(f"[CHECK] {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        response = session.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True,
        )
    except requests.RequestException as error:
        return {
            "页面标题": "",
            "HTTP状态码": "",
            "是否跳转": "未确认",
            "访问状态": f"访问失败：{error}",
            "平台类型": "不可访问",
            "是否公开": "否",
            "需要登录": "未确认",
            "支持搜索": "未确认",
            "是否可采集": "否",
            "验证结果": "不可访问",
            "最后检查时间": checked_time,
        }

    title, page_text = parse_page(response)
    is_redirected = response.url.rstrip("/") != url.rstrip("/")
    is_login = is_login_page(page_text, title, response.url)
    is_public_notice = contains_any(page_text, PUBLIC_NOTICE_KEYWORDS)
    is_supplier_portal = contains_any(page_text, SUPPLIER_PORTAL_KEYWORDS)
    supports_search = detect_search_support(page_text)
    platform_type = detect_platform_type(
        response.status_code,
        is_login,
        is_public_notice,
        is_supplier_portal,
    )
    is_collectable = (
        response.status_code < 400
        and is_public_notice
        and not is_login
    )

    return {
        "页面标题": title,
        "HTTP状态码": str(response.status_code),
        "是否跳转": "是" if is_redirected else "否",
        "访问状态": build_access_status(response.status_code, is_redirected),
        "平台类型": platform_type,
        "是否公开": "是" if is_public_notice and not is_login else "否",
        "需要登录": "是" if is_login else "否",
        "支持搜索": "是" if supports_search else "否",
        "是否可采集": "是" if is_collectable else "否",
        "验证结果": build_validation_result(platform_type, is_collectable),
        "最后检查时间": checked_time,
    }


def build_empty_url_result(checked_time):
    return {
        "页面标题": "",
        "HTTP状态码": "",
        "是否跳转": "未确认",
        "访问状态": "未填写采购平台网址",
        "平台类型": "未知",
        "是否公开": "未确认",
        "需要登录": "未确认",
        "支持搜索": "未确认",
        "是否可采集": "否",
        "验证结果": "待补充网址",
        "最后检查时间": checked_time,
    }


def parse_page(response):
    response.encoding = response.apparent_encoding

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception:
        return "", ""

    title = ""

    if soup.title:
        title = soup.title.get_text(" ", strip=True)

    page_text = soup.get_text(" ", strip=True)
    return title, page_text


def detect_platform_type(status_code, is_login, is_public_notice, is_supplier_portal):
    if status_code >= 400:
        return "不可访问"

    if is_public_notice and not is_login:
        return "公开公告平台"

    if is_login:
        return "登录采购平台"

    if is_supplier_portal:
        return "供应商门户"

    return "未知"


def detect_search_support(page_text):
    return contains_any(page_text, SEARCH_KEYWORDS)


def build_access_status(status_code, is_redirected):
    redirect_text = "，发生跳转" if is_redirected else "，未跳转"
    return f"HTTP {status_code}{redirect_text}"


def build_validation_result(platform_type, is_collectable):
    if is_collectable:
        return "可公开采集"

    if platform_type == "登录采购平台":
        return "登录页"

    if platform_type == "不可访问":
        return "不可访问"

    if platform_type == "供应商门户":
        return "供应商门户，需人工确认"

    return "需人工确认"


def is_login_url(url):
    path = urlparse(url).path.lower()
    return "login" in path or "signin" in path


def is_login_page(page_text, title, url):
    if is_login_url(url):
        return True

    if is_procurement_javascript_app(page_text, title):
        return True

    return count_keyword_matches(page_text, LOGIN_KEYWORDS) >= LOGIN_KEYWORD_THRESHOLD


def is_procurement_javascript_app(page_text, title):
    combined_text = f"{title} {page_text}"

    return (
        contains_any(combined_text, PROCUREMENT_APP_KEYWORDS)
        and contains_any(combined_text, JAVASCRIPT_APP_KEYWORDS)
    )


def count_keyword_matches(text, keywords):
    text_lower = str(text).lower()

    return sum(
        1
        for keyword in keywords
        if keyword.lower() in text_lower
    )


def contains_any(text, keywords):
    text_lower = str(text).lower()

    return any(keyword.lower() in text_lower for keyword in keywords)


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


def print_validation_stats(stats):
    print(f"[DONE] Total: {stats['total']}")
    print(f"[DONE] Public platforms: {stats['public_platform']}")
    print(f"[DONE] Login platforms: {stats['login_platform']}")
    print(f"[DONE] Unavailable: {stats['unavailable']}")
    print(f"[DONE] Collectable: {stats['collectable']}")


def _file_fingerprint(path):
    status_path = Path(path)
    digest = hashlib.sha256()

    try:
        with status_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise EnterpriseStatusChangedError(
            f"Unable to fingerprint enterprise status file: {status_path}"
        ) from error

    stat = status_path.stat()
    return {
        "sha256": digest.hexdigest(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _assert_file_unchanged(path, original_fingerprint):
    current_fingerprint = _file_fingerprint(path)
    if current_fingerprint != original_fingerprint:
        raise EnterpriseStatusChangedError(
            "Enterprise status file changed during validation; write aborted: "
            f"{Path(path)}"
        )


if __name__ == "__main__":
    validate_enterprise_urls()
