"""
PackagingRadar V6.5 path registry.

Keep business data file locations here so directory changes only require
editing this module.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

BID_RESULTS = BASE_DIR / "bid_results.xlsx"
CUSTOMER_POOL = BASE_DIR / "customer_pool.xlsx"
FOLLOWUP_TASKS = BASE_DIR / "followup_tasks.xlsx"
ENTERPRISE_URL_STATUS = BASE_DIR / "enterprise_url_status.xlsx"
TARGET_COMPANIES = BASE_DIR / "target_companies.xlsx"
HIGH_VALUE_LEADS = BASE_DIR / "high_value_leads.xlsx"
CUSTOMER_CONTACT_CANDIDATES = BASE_DIR / "customer_contact_candidates.xlsx"

BID_RESULTS_FILE = BID_RESULTS
CUSTOMER_POOL_FILE = CUSTOMER_POOL
FOLLOWUP_TASKS_FILE = FOLLOWUP_TASKS
ENTERPRISE_URL_STATUS_FILE = ENTERPRISE_URL_STATUS
TARGET_COMPANIES_FILE = TARGET_COMPANIES
HIGH_VALUE_LEADS_FILE = HIGH_VALUE_LEADS

CORE_DATA_FILES = {
    "bid_results": BID_RESULTS,
    "customer_pool": CUSTOMER_POOL,
    "followup_tasks": FOLLOWUP_TASKS,
    "enterprise_url_status": ENTERPRISE_URL_STATUS,
    "target_companies": TARGET_COMPANIES,
    "high_value_leads": HIGH_VALUE_LEADS,
    "customer_contact_candidates": CUSTOMER_CONTACT_CANDIDATES,
}
