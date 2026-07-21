"""
PackagingRadar V6.5 path registry.

Keep business data file locations here so directory changes only require
editing this module.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT

BID_RESULTS_FILE = PROJECT_ROOT / "bid_results.xlsx"
CUSTOMER_POOL_FILE = PROJECT_ROOT / "customer_pool.xlsx"
FOLLOWUP_TASKS_FILE = PROJECT_ROOT / "followup_tasks.xlsx"
ENTERPRISE_URL_STATUS_FILE = PROJECT_ROOT / "enterprise_url_status.xlsx"
ENTERPRISE_CANDIDATES_FILE = PROJECT_ROOT / "enterprise_candidates.xlsx"
TARGET_COMPANIES_FILE = PROJECT_ROOT / "target_companies.xlsx"
HIGH_VALUE_LEADS_FILE = PROJECT_ROOT / "high_value_leads.xlsx"
CUSTOMER_CONTACT_CANDIDATES_FILE = PROJECT_ROOT / "customer_contact_candidates.xlsx"

PRODUCTION_PROJECTS_FILE = PROJECT_ROOT / "production_projects.xlsx"
EIA_PROJECTS_FILE = PROJECT_ROOT / "eia_projects.xlsx"
EXPANSION_PROJECTS_FILE = PROJECT_ROOT / "expansion_projects.xlsx"

RAW_RESULTS_DEBUG_FILE = PROJECT_ROOT / "raw_results_debug.xlsx"
RAW_JIANYU_RESULTS_FILE = PROJECT_ROOT / "raw_jianyu_results.xlsx"
EIA_RAW_RESULTS_FILE = PROJECT_ROOT / "eia_raw_results.xlsx"
EIA_RAW_DEBUG_FILE = PROJECT_ROOT / "eia_raw_debug.xlsx"
PRODUCTION_RAW_DEBUG_FILE = PROJECT_ROOT / "production_raw_debug.xlsx"

MANUAL_IMPORT_FILE = PROJECT_ROOT / "manual_import.xlsx"
DAILY_REPORT_FILE = PROJECT_ROOT / "daily_report.txt"
EIA_DIAGNOSIS_FILE = PROJECT_ROOT / "eia_diagnosis.txt"

# Backward-compatible aliases used by scripts migrated in V6.5.
BID_RESULTS = BID_RESULTS_FILE
CUSTOMER_POOL = CUSTOMER_POOL_FILE
FOLLOWUP_TASKS = FOLLOWUP_TASKS_FILE
ENTERPRISE_URL_STATUS = ENTERPRISE_URL_STATUS_FILE
TARGET_COMPANIES = TARGET_COMPANIES_FILE
HIGH_VALUE_LEADS = HIGH_VALUE_LEADS_FILE
CUSTOMER_CONTACT_CANDIDATES = CUSTOMER_CONTACT_CANDIDATES_FILE

CORE_DATA_FILES = {
    "bid_results": BID_RESULTS,
    "customer_pool": CUSTOMER_POOL,
    "followup_tasks": FOLLOWUP_TASKS,
    "enterprise_url_status": ENTERPRISE_URL_STATUS,
    "enterprise_candidates": ENTERPRISE_CANDIDATES_FILE,
    "target_companies": TARGET_COMPANIES,
    "high_value_leads": HIGH_VALUE_LEADS,
    "customer_contact_candidates": CUSTOMER_CONTACT_CANDIDATES,
    "production_projects": PRODUCTION_PROJECTS_FILE,
    "eia_projects": EIA_PROJECTS_FILE,
    "expansion_projects": EXPANSION_PROJECTS_FILE,
    "raw_results_debug": RAW_RESULTS_DEBUG_FILE,
    "raw_jianyu_results": RAW_JIANYU_RESULTS_FILE,
    "eia_raw_results": EIA_RAW_RESULTS_FILE,
    "eia_raw_debug": EIA_RAW_DEBUG_FILE,
    "production_raw_debug": PRODUCTION_RAW_DEBUG_FILE,
    "manual_import": MANUAL_IMPORT_FILE,
    "daily_report": DAILY_REPORT_FILE,
    "eia_diagnosis": EIA_DIAGNOSIS_FILE,
}
