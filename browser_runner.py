import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from contextlib import contextmanager
import os


DEFAULT_VIEWPORT = {
    "width": 1366,
    "height": 900,
}


@contextmanager
def open_browser(headless=False, slow_mo=120):
    """
    Open a Playwright Chromium browser for assisted public-page collection.

    This runner only provides normal browser automation. It does not log in,
    bypass CAPTCHA, or work around access limits.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install playwright && "
            "python -m playwright install chromium"
        ) from error

    playwright = sync_playwright().start()
    browser = None

    try:
        browser = launch_chromium(playwright, PlaywrightError, headless, slow_mo)
        context = browser.new_context(
            viewport=DEFAULT_VIEWPORT,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = context.new_page()
        yield page
    finally:
        if browser is not None:
            browser.close()
        playwright.stop()


def launch_chromium(playwright, playwright_error, headless, slow_mo):
    try:
        return playwright.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
        )
    except playwright_error as bundled_error:
        for executable_path in get_windows_browser_paths():
            if not os.path.exists(executable_path):
                continue

            try:
                return playwright.chromium.launch(
                    executable_path=executable_path,
                    headless=headless,
                    slow_mo=slow_mo,
                )
            except playwright_error:
                continue

        raise RuntimeError(
            "No usable Chromium browser found. Install Playwright Chromium with "
            "`python -m playwright install chromium`, or install Chrome/Edge."
        ) from bundled_error


def get_windows_browser_paths():
    program_files = os.environ.get("ProgramFiles", "")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    return [
        os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(local_app_data, "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
