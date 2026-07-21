import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from candidate_contact_importer import (
    CANDIDATE_COLUMNS,
    import_confirmed_contacts,
)
from customer_pool import (
    CUSTOMER_COLUMNS,
    HIGH_VALUE_COLUMNS,
    TARGET_COLUMNS,
    build_customer_pool,
)
from paths import CUSTOMER_CONTACT_CANDIDATES, CUSTOMER_POOL
from utils.excel_helper import ExcelWriteError, read_excel_safe


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_for(columns, **values):
    row = {column: "" for column in columns}
    row.update(values)
    return row


class CustomerPoolSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formal_hashes = {
            Path(CUSTOMER_POOL): file_hash(CUSTOMER_POOL),
            Path(CUSTOMER_CONTACT_CANDIDATES): file_hash(
                CUSTOMER_CONTACT_CANDIDATES
            ),
        }

    @classmethod
    def tearDownClass(cls):
        for path, expected_hash in cls.formal_hashes.items():
            if file_hash(path) != expected_hash:
                raise AssertionError(f"Formal workbook was modified: {path}")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_customer_inputs(self):
        high_value_file = self.directory / "high_value.xlsx"
        target_file = self.directory / "targets.xlsx"
        pool_file = self.directory / "customer_pool.xlsx"

        leads = [
            row_for(
                HIGH_VALUE_COLUMNS,
                **{
                    "招标标题": "更新后的纸箱项目",
                    "采购单位": "甲公司",
                    "省份": "江苏",
                    "城市": "苏州",
                    "价值分数": 80,
                },
            ),
            row_for(
                HIGH_VALUE_COLUMNS,
                **{
                    "招标标题": "同企业第二条项目",
                    "采购单位": "甲公司",
                    "价值分数": 70,
                },
            ),
            row_for(
                HIGH_VALUE_COLUMNS,
                **{
                    "招标标题": "乙公司纸箱项目",
                    "采购单位": "乙公司",
                    "价值分数": 60,
                },
            ),
        ]
        targets = [
            row_for(
                TARGET_COLUMNS,
                **{
                    "企业名称": "甲公司",
                    "行业": "食品",
                    "官网": "https://a.example.com",
                    "电话": "025-12345678",
                },
            )
        ]
        existing = row_for(
            CUSTOMER_COLUMNS,
            **{
                "企业名称": "甲公司",
                "来源": "人工维护",
                "招标标题": "旧项目",
                "省份": "江苏",
                "首次发现日期": "2026-01-01",
                "开发状态": "跟进中",
                "优先级": "A",
                "价值分数": 50,
                "电话": "025-87654321",
                "备注": "人工备注不得覆盖",
            },
        )
        existing["人工标签"] = "重点客户"
        ordered_columns = [
            "企业名称",
            "人工标签",
            *[column for column in CUSTOMER_COLUMNS if column != "企业名称"],
        ]

        pd.DataFrame(leads, columns=HIGH_VALUE_COLUMNS).to_excel(
            high_value_file, index=False, engine="openpyxl"
        )
        pd.DataFrame(targets, columns=TARGET_COLUMNS).to_excel(
            target_file, index=False, engine="openpyxl"
        )
        pd.DataFrame([existing], columns=ordered_columns).to_excel(
            pool_file, index=False, engine="openpyxl"
        )
        return high_value_file, target_file, pool_file, ordered_columns

    def test_customer_result_rules_extra_fields_order_and_no_duplicates(self):
        high_value_file, target_file, pool_file, ordered_columns = (
            self._write_customer_inputs()
        )

        stats = build_customer_pool(high_value_file, target_file, pool_file)
        result = read_excel_safe(pool_file).fillna("")

        self.assertEqual(stats, {
            "total": 2,
            "new": 1,
            "existing": 1,
            "output_file": pool_file,
        })
        self.assertEqual(list(result.columns), ordered_columns)
        self.assertEqual(result["企业名称"].nunique(), 2)
        self.assertEqual(list(result["企业名称"]).count("甲公司"), 1)

        existing = result[result["企业名称"] == "甲公司"].iloc[0]
        self.assertEqual(existing["来源"], "人工维护、高价值线索")
        self.assertEqual(existing["招标标题"], "同企业第二条项目")
        self.assertEqual(existing["价值分数"], 80)
        self.assertEqual(existing["电话"], "025-87654321")
        self.assertEqual(existing["备注"], "人工备注不得覆盖")
        self.assertEqual(existing["人工标签"], "重点客户")

        new_customer = result[result["企业名称"] == "乙公司"].iloc[0]
        self.assertEqual(new_customer["来源"], "高价值线索")
        self.assertEqual(new_customer["开发状态"], "待开发")
        self.assertEqual(new_customer["优先级"], "高")
        self.assertEqual(new_customer["价值分数"], 60)
        self.assertTrue(list(self.directory.glob("backup/auto/customer_pool/*.xlsx")))

    def test_customer_write_failure_preserves_existing_file(self):
        high_value_file, target_file, pool_file, _ = self._write_customer_inputs()
        original_hash = file_hash(pool_file)

        with mock.patch("utils.excel_helper.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(ExcelWriteError):
                build_customer_pool(high_value_file, target_file, pool_file)

        self.assertEqual(file_hash(pool_file), original_hash)

    def test_contact_import_preserves_existing_contact_remark_and_extra_field(self):
        candidates_file = self.directory / "candidates.xlsx"
        pool_file = self.directory / "customer_pool.xlsx"
        candidates = [
            row_for(
                CANDIDATE_COLUMNS,
                **{
                    "企业名称": "甲公司",
                    "候选网址": "https://a.example.com",
                    "候选电话": "025-00000000",
                    "候选邮箱": "new@example.com",
                    "搜索关键词": "官网",
                    "是否确认": "是",
                },
            ),
            row_for(
                CANDIDATE_COLUMNS,
                **{
                    "企业名称": "甲公司",
                    "候选邮箱": "ignored@example.com",
                    "是否确认": "否",
                },
            ),
        ]
        pool_columns = ["人工标签", *CUSTOMER_COLUMNS]
        customer = row_for(
            pool_columns,
            **{
                "人工标签": "保留",
                "企业名称": "甲公司",
                "电话": "025-12345678",
                "备注": "原人工备注",
            },
        )
        pd.DataFrame(candidates, columns=CANDIDATE_COLUMNS).to_excel(
            candidates_file, index=False, engine="openpyxl"
        )
        pd.DataFrame([customer], columns=pool_columns).to_excel(
            pool_file, index=False, engine="openpyxl"
        )

        stats = import_confirmed_contacts(candidates_file, pool_file)
        result = read_excel_safe(pool_file).fillna("")

        self.assertEqual(stats["confirmed"], 1)
        self.assertEqual(stats["imported"], 1)
        self.assertEqual(list(result.columns), pool_columns)
        self.assertEqual(result.at[0, "电话"], "025-12345678")
        self.assertEqual(result.at[0, "邮箱"], "new@example.com")
        self.assertEqual(result.at[0, "官网"], "https://a.example.com")
        self.assertEqual(result.at[0, "人工标签"], "保留")
        self.assertIn("原人工备注", result.at[0, "备注"])
        self.assertIn("联系方式已确认导入", result.at[0, "备注"])
        self.assertNotIn("ignored@example.com", result.to_string())


if __name__ == "__main__":
    unittest.main()
