import hashlib
import importlib
import os
import re
import tempfile
import unittest
from pathlib import Path, PurePosixPath, PureWindowsPath

import paths


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PATHS = {
    "BID_RESULTS_FILE": "bid_results.xlsx",
    "CUSTOMER_POOL_FILE": "customer_pool.xlsx",
    "FOLLOWUP_TASKS_FILE": "followup_tasks.xlsx",
    "ENTERPRISE_URL_STATUS_FILE": "enterprise_url_status.xlsx",
    "ENTERPRISE_CANDIDATES_FILE": "enterprise_candidates.xlsx",
    "TARGET_COMPANIES_FILE": "target_companies.xlsx",
    "HIGH_VALUE_LEADS_FILE": "high_value_leads.xlsx",
    "CUSTOMER_CONTACT_CANDIDATES_FILE": "customer_contact_candidates.xlsx",
    "PRODUCTION_PROJECTS_FILE": "production_projects.xlsx",
    "EIA_PROJECTS_FILE": "eia_projects.xlsx",
    "EXPANSION_PROJECTS_FILE": "expansion_projects.xlsx",
    "RAW_RESULTS_DEBUG_FILE": "raw_results_debug.xlsx",
    "RAW_JIANYU_RESULTS_FILE": "raw_jianyu_results.xlsx",
    "EIA_RAW_RESULTS_FILE": "eia_raw_results.xlsx",
    "EIA_RAW_DEBUG_FILE": "eia_raw_debug.xlsx",
    "PRODUCTION_RAW_DEBUG_FILE": "production_raw_debug.xlsx",
    "MANUAL_IMPORT_FILE": "manual_import.xlsx",
    "DAILY_REPORT_FILE": "daily_report.txt",
    "EIA_DIAGNOSIS_FILE": "eia_diagnosis.txt",
}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PathRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formal_hashes = {
            path: file_hash(path)
            for pattern in ("*.xlsx", "*.txt")
            for path in ROOT.glob(pattern)
        }

    @classmethod
    def tearDownClass(cls):
        for path, expected_hash in cls.formal_hashes.items():
            if file_hash(path) != expected_hash:
                raise AssertionError(f"Formal data file was modified: {path}")

    def test_all_registered_paths_are_absolute_project_root_paths(self):
        self.assertEqual(paths.PROJECT_ROOT, ROOT)
        self.assertEqual(paths.BASE_DIR, ROOT)

        for constant_name, file_name in EXPECTED_PATHS.items():
            with self.subTest(constant=constant_name):
                value = getattr(paths, constant_name)
                self.assertIsInstance(value, Path)
                self.assertTrue(value.is_absolute())
                self.assertEqual(value.parent, ROOT)
                self.assertEqual(value.name, file_name)

    def test_registry_contains_every_declared_business_data_path(self):
        registered = set(paths.CORE_DATA_FILES.values())
        expected = {getattr(paths, name) for name in EXPECTED_PATHS}
        self.assertEqual(registered, expected)

    def test_path_names_are_windows_and_mac_compatible(self):
        for file_name in EXPECTED_PATHS.values():
            with self.subTest(file=file_name):
                self.assertEqual(PureWindowsPath("C:/BidRadar", file_name).name, file_name)
                self.assertEqual(PurePosixPath("/BidRadar", file_name).name, file_name)
                self.assertNotIn("/", file_name)
                self.assertNotIn("\\", file_name)

    def test_paths_do_not_depend_on_current_working_directory(self):
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                reloaded = importlib.reload(paths)
                for constant_name, file_name in EXPECTED_PATHS.items():
                    self.assertEqual(
                        getattr(reloaded, constant_name),
                        ROOT / file_name,
                    )
            finally:
                os.chdir(original_cwd)
                importlib.reload(paths)

    def test_business_scripts_have_no_local_excel_or_txt_path_literals(self):
        excluded = {"paths.py", "test_sample_run.py"}
        literal_pattern = re.compile(r"[\"']([^\"']+\.(?:xlsx|txt))[\"']")

        violations = []
        for script in ROOT.glob("*.py"):
            if script.name in excluded:
                continue
            for match in literal_pattern.finditer(script.read_text(encoding="utf-8")):
                violations.append(f"{script.name}: {match.group(1)}")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
