import hashlib
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import pandas as pd

import followup_manager
from customer_pool import CUSTOMER_COLUMNS
from followup_manager import (
    FOLLOWUP_COLUMNS,
    TASK_COLUMNS,
    build_followup_tasks,
    build_task,
    ensure_followup_columns,
    sort_tasks,
)
from paths import CUSTOMER_POOL, FOLLOWUP_TASKS
from utils.excel_helper import ExcelWriteError, read_excel_safe, write_excel_safe


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_expected_outputs(customer_df):
    expected_customer = ensure_followup_columns(customer_df.copy())
    tasks = []
    for _, row in expected_customer.iterrows():
        task = build_task(row, date.today())
        if task is not None:
            tasks.append(task)
    expected_tasks = pd.DataFrame(tasks)
    for column in TASK_COLUMNS:
        if column not in expected_tasks.columns:
            expected_tasks[column] = ""
    return expected_customer, sort_tasks(expected_tasks[TASK_COLUMNS])


class FollowupSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formal_hashes = {
            Path(CUSTOMER_POOL): file_hash(CUSTOMER_POOL),
            Path(FOLLOWUP_TASKS): file_hash(FOLLOWUP_TASKS),
        }

    @classmethod
    def tearDownClass(cls):
        for path, expected_hash in cls.formal_hashes.items():
            if file_hash(path) != expected_hash:
                raise AssertionError(f"Formal workbook was modified: {path}")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.customer_file = self.directory / "customer_pool.xlsx"
        self.task_file = self.directory / "followup_tasks.xlsx"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_existing_files(self):
        columns = ["人工标签", *CUSTOMER_COLUMNS]
        rows = []
        for values in [
            {
                "企业名称": "甲公司",
                "行业": "食品",
                "开发状态": "待开发",
                "电话": "025-12345678",
                "备注": "人工备注",
                "人工标签": "重点",
            },
            {
                "企业名称": "乙公司",
                "行业": "电子",
                "开发状态": "已开发",
                "最后跟进日期": "2020-01-01",
                "人工标签": "观察",
            },
        ]:
            row = {column: "" for column in columns}
            row.update(values)
            rows.append(row)
        customer_df = pd.DataFrame(rows, columns=columns)
        old_tasks = pd.DataFrame(
            [{column: "旧任务" if column == "企业名称" else "" for column in TASK_COLUMNS}],
            columns=TASK_COLUMNS,
        )
        customer_df.to_excel(self.customer_file, index=False, engine="openpyxl")
        old_tasks.to_excel(self.task_file, index=False, engine="openpyxl")
        return customer_df, columns

    def test_followup_results_match_existing_rules_and_preserve_column_order(self):
        customer_df, original_columns = self._write_existing_files()
        expected_customer, expected_tasks = build_expected_outputs(customer_df)

        stats = build_followup_tasks(self.customer_file, self.task_file)
        actual_customer = read_excel_safe(self.customer_file).fillna("")
        actual_tasks = read_excel_safe(self.task_file).fillna("")

        expected_columns = original_columns + [
            column for column in FOLLOWUP_COLUMNS if column not in original_columns
        ]
        self.assertEqual(list(actual_customer.columns), expected_columns)
        pd.testing.assert_frame_equal(
            actual_customer.reset_index(drop=True),
            expected_customer.fillna("").reset_index(drop=True),
            check_dtype=False,
        )
        pd.testing.assert_frame_equal(
            actual_tasks.reset_index(drop=True),
            expected_tasks.fillna("").reset_index(drop=True),
            check_dtype=False,
        )
        self.assertEqual(stats["total_customers"], 2)
        self.assertEqual(stats["pending_count"], 1)
        self.assertEqual(list(actual_tasks.columns), TASK_COLUMNS)
        self.assertEqual(actual_customer.at[0, "人工标签"], "重点")
        self.assertEqual(actual_customer.at[0, "备注"], "人工备注")
        self.assertTrue(list(self.directory.glob("backup/auto/customer_pool/*.xlsx")))
        self.assertTrue(list(self.directory.glob("backup/auto/followup_tasks/*.xlsx")))

    def test_second_write_failure_restores_both_previous_files(self):
        self._write_existing_files()
        customer_hash = file_hash(self.customer_file)
        task_hash = file_hash(self.task_file)
        calls = 0

        def fail_second_write(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise ExcelWriteError("simulated second output failure")
            return write_excel_safe(*args, **kwargs)

        with mock.patch.object(
            followup_manager,
            "write_excel_safe",
            side_effect=fail_second_write,
        ):
            with self.assertRaisesRegex(
                ExcelWriteError,
                "previous files were restored",
            ):
                build_followup_tasks(self.customer_file, self.task_file)

        self.assertEqual(file_hash(self.customer_file), customer_hash)
        self.assertEqual(file_hash(self.task_file), task_hash)

    def test_failure_removes_task_file_that_did_not_exist_before_run(self):
        self._write_existing_files()
        self.task_file.unlink()
        customer_hash = file_hash(self.customer_file)

        with mock.patch.object(
            followup_manager,
            "write_excel_safe",
            side_effect=ExcelWriteError("simulated failure"),
        ):
            with self.assertRaises(ExcelWriteError):
                build_followup_tasks(self.customer_file, self.task_file)

        self.assertEqual(file_hash(self.customer_file), customer_hash)
        self.assertFalse(self.task_file.exists())


if __name__ == "__main__":
    unittest.main()
