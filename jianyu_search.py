import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import datetime
import re
import time
from urllib.parse import quote_plus, urljoin

import pandas as pd

from browser_runner import open_browser
from keywords import KEYWORDS


JIAN_YU_HOME = "https://www.jianyu360.com"
OUTPUT_FILE = "raw_jianyu_results.xlsx"
WAIT_BETWEEN_KEYWORDS_SECONDS = 5

RESULT_COLUMNS = [
    "搜索关键词",
    "标题",
    "链接",
    "发布时间",
    "来源",
    "采集时间",
]

ACCESS_LIMIT_WORDS = [
    "验证码",
    "请登录",
    "登录后",
    "访问过于频繁",
    "安全验证",
    "人机验证",
    "captcha",
]

SEARCH_INPUT_SELECTORS = [
    "input[placeholder*='搜索']",
    "input[placeholder*='关键词']",
    "input[placeholder*='请输入']",
    "input[type='search']",
    "input[type='text']",
]

DATE_PATTERN = re.compile(
    r"((?:20\d{2})[-/.年](?:0?[1-9]|1[0-2])[-/.月](?:0?[1-9]|[12]\d|3[01])日?)"
)


def search_jianyu_keywords(
    keywords=None,
    output_file=OUTPUT_FILE,
    headless=False,
    wait_seconds=WAIT_BETWEEN_KEYWORDS_SECONDS,
):
    if keywords is None:
        keywords = KEYWORDS

    all_results = []

    with open_browser(headless=headless) as page:
        for keyword in keywords:
            keyword_results = []

            try:
                keyword_results = search_one_keyword(page, keyword)
            except Exception as error:
                print(f"[ERROR] Keyword skipped: {keyword}; reason: {error}")

            all_results.extend(keyword_results)
            print(f"关键词：{keyword}")
            print(f"获取数量：{len(keyword_results)}")

            if wait_seconds > 0:
                time.sleep(wait_seconds)

    export_results(all_results, output_file)
    print(f"导出文件：{output_file}")
    return all_results


def search_one_keyword(page, keyword):
    page.goto(JIAN_YU_HOME, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)

    if has_access_limit(page):
        print(f"[ERROR] Access limited before search: {keyword}")
        return []

    search_input = find_search_input(page)

    if search_input is None:
        print(f"[ERROR] Search input not found: {keyword}")
        return []

    search_input.click(timeout=5000)
    search_input.fill(keyword, timeout=5000)
    search_input.press("Enter", timeout=5000)

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        page.wait_for_timeout(3000)

    page.wait_for_timeout(1500)

    if has_access_limit(page):
        print(f"[ERROR] Access limited after search: {keyword}")
        return []

    return extract_visible_results(page, keyword)


def find_search_input(page):
    for selector in SEARCH_INPUT_SELECTORS:
        locator = page.locator(selector).first

        try:
            if locator.count() and locator.is_visible(timeout=1500):
                return locator
        except Exception:
            continue

    return None


def has_access_limit(page):
    try:
        body_text = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        return False

    return any(word.lower() in body_text for word in ACCESS_LIMIT_WORDS)


def extract_visible_results(page, keyword):
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    raw_results = page.evaluate(
        """
        () => {
            const rows = [];
            const resultItems = Array.from(
                document.querySelectorAll('.article-item.list-item')
            );

            for (const item of resultItems) {
                const rect = item.getBoundingClientRect();

                if (rect.width <= 0 || rect.height <= 0) {
                    continue;
                }

                const titleElement = item.querySelector('.a-i-left');
                const timeElement = item.querySelector('.time-text');
                const dataElement = item.querySelector('input[dataid]');
                const title = (titleElement?.innerText || '').trim();
                const dataid = dataElement?.getAttribute('dataid') || '';

                if (!title) {
                    continue;
                }

                rows.push({
                    title,
                    dataid,
                    time: (timeElement?.innerText || '').trim(),
                    text: (item.innerText || '').trim(),
                });
            }

            return rows;
        }
        """
    )

    results = []
    seen = set()

    for raw_result in raw_results:
        title = clean_result_title(raw_result.get("title", ""))
        link = build_result_link(raw_result.get("dataid", ""), keyword, page.url)

        if not is_probable_result(title, link):
            continue

        key = (keyword, link)

        if key in seen:
            continue

        seen.add(key)
        container_text = clean_text(raw_result.get("text", ""))

        results.append(
            {
                "搜索关键词": keyword,
                "标题": title,
                "链接": link,
                "发布时间": extract_publish_time(
                    raw_result.get("time", "") or container_text
                ),
                "来源": "剑鱼标讯",
                "采集时间": collected_at,
            }
        )

    return results


def is_probable_result(title, link):
    if len(title) < 6:
        return False

    if "jianyu360.cn" not in link and "jianyu360.com" not in link:
        return False

    ignored_parts = [
        "/login/",
        "/login?",
        "/register",
        "javascript:",
        "#",
    ]

    if any(part in link.lower() for part in ignored_parts):
        return False

    ignored_titles = {
        "首页",
        "登录",
        "注册",
        "免费注册",
        "会员中心",
        "剑鱼标讯",
    }

    return title not in ignored_titles


def extract_publish_time(text):
    match = DATE_PATTERN.search(text)

    if not match:
        return ""

    return (
        match.group(1)
        .replace("年", "-")
        .replace("月", "-")
        .replace("日", "")
        .replace("/", "-")
        .replace(".", "-")
    )


def export_results(results, output_file=OUTPUT_FILE):
    df = pd.DataFrame(results)

    for column in RESULT_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[RESULT_COLUMNS]

    if not df.empty:
        df = df.drop_duplicates(
            subset=["搜索关键词", "链接"],
            keep="first",
        )

    df.to_excel(output_file, index=False, engine="openpyxl")
    return output_file


def clean_text(value):
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_result_title(value):
    title = clean_text(value)
    return re.sub(r"^\d+\.\s*", "", title).strip()


def build_result_link(dataid, keyword, fallback_url):
    dataid = clean_text(dataid)

    if dataid:
        path = f"/nologin/content/{dataid}.html?kds={quote_plus(keyword)}"
        return urljoin(fallback_url, path)

    return clean_text(fallback_url)


if __name__ == "__main__":
    try:
        search_jianyu_keywords()
    except RuntimeError as error:
        print(f"[ERROR] {error}")
        raise SystemExit(1)
