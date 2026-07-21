import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

import enterprise_validator
from candidate_importer import import_confirmed_candidates
from candidate_ranker import rank_candidates, score_candidate
from enterprise_source_manager import (
    STATUS_COLUMNS,
    create_enterprise_url_status_file,
)
from enterprise_validator import (
    EnterpriseStatusChangedError,
    VALIDATION_COLUMNS,
    validate_enterprise_urls,
)
from paths import ENTERPRISE_URL_STATUS
from source_discovery import CANDIDATE_COLUMNS, export_candidates
from utils.excel_helper import ExcelWriteError, read_excel_safe


FORMAL_CANDIDATES = Path(__file__).resolve().parents[1] / "enterprise_candidates.xlsx"


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_for(columns, **values):
    row = {column: "" for column in columns}
    row.update(values)
    return row


class EnterpriseStatusSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formal_hashes = {
            Path(ENTERPRISE_URL_STATUS): file_hash(ENTERPRISE_URL_STATUS),
            FORMAL_CANDIDATES: file_hash(FORMAL_CANDIDATES),
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

    def test_source_manager_preserves_existing_status_and_manual_fields(self):
        status_file = self.directory / "enterprise_url_status.xlsx"
        existing_columns = ["人工负责人", *STATUS_COLUMNS, "人工结论"]
        existing = row_for(
            existing_columns,
            **{
                "人工负责人": "张三",
                "企业名称": "甲公司",
                "行业": "食品",
                "采购平台网址": "https://manual.example.com",
                "是否公开": "人工确认",
                "是否验证": "是",
                "备注": "人工备注",
                "人工结论": "保留",
            },
        )
        pd.DataFrame([existing], columns=existing_columns).to_excel(
            status_file, index=False, engine="openpyxl"
        )
        sources = [
            {
                "name": "甲公司",
                "industry": "食品",
                "homepage": "https://a.example.com",
                "procurement_url": "https://config.example.com",
                "priority": "A",
            },
            {
                "name": "乙公司",
                "industry": "电子",
                "homepage": "https://b.example.com",
                "procurement_url": "",
                "priority": "B",
            },
        ]

        with mock.patch(
            "enterprise_source_manager.build_enterprise_url_status",
            return_value=[
                row_for(
                    STATUS_COLUMNS,
                    **{
                        "企业名称": source["name"],
                        "行业": source["industry"],
                        "官网": source["homepage"],
                        "采购平台网址": source["procurement_url"],
                        "优先级": source["priority"],
                        "是否公开": "未确认",
                        "需要登录": "未确认",
                        "支持搜索": "未确认",
                        "是否验证": "否",
                    },
                )
                for source in sources
            ],
        ):
            create_enterprise_url_status_file(status_file)

        result = read_excel_safe(status_file).fillna("")
        self.assertEqual(list(result.columns), existing_columns)
        self.assertEqual(result["企业名称"].nunique(), 2)
        saved = result[result["企业名称"] == "甲公司"].iloc[0]
        self.assertEqual(saved["采购平台网址"], "https://manual.example.com")
        self.assertEqual(saved["是否公开"], "人工确认")
        self.assertEqual(saved["是否验证"], "是")
        self.assertEqual(saved["备注"], "人工备注")
        self.assertEqual(saved["人工负责人"], "张三")
        self.assertEqual(saved["人工结论"], "保留")

    def test_candidate_import_keeps_unconfirmed_and_existing_url_rules(self):
        candidates_file = self.directory / "enterprise_candidates.xlsx"
        status_file = self.directory / "enterprise_url_status.xlsx"
        candidate_columns = ["企业名称", "候选网址", "是否确认", "人工评分"]
        candidates = [
            {
                "企业名称": "甲公司",
                "候选网址": "https://confirmed.example.com",
                "是否确认": "是",
                "人工评分": "高",
            },
            {
                "企业名称": "乙公司",
                "候选网址": "https://unconfirmed.example.com",
                "是否确认": "否",
                "人工评分": "高",
            },
            {
                "企业名称": "丙公司",
                "候选网址": "https://replacement.example.com",
                "是否确认": "是",
                "人工评分": "高",
            },
        ]
        status_columns = ["人工负责人", *STATUS_COLUMNS]
        statuses = [
            row_for(status_columns, **{"企业名称": "甲公司", "人工负责人": "A"}),
            row_for(status_columns, **{"企业名称": "乙公司", "人工负责人": "B"}),
            row_for(
                status_columns,
                **{
                    "企业名称": "丙公司",
                    "采购平台网址": "https://existing.example.com",
                    "备注": "旧备注",
                    "人工负责人": "C",
                },
            ),
        ]
        pd.DataFrame(candidates, columns=candidate_columns).to_excel(
            candidates_file, index=False, engine="openpyxl"
        )
        pd.DataFrame(statuses, columns=status_columns).to_excel(
            status_file, index=False, engine="openpyxl"
        )

        stats = import_confirmed_candidates(candidates_file, status_file)
        result = read_excel_safe(status_file).fillna("")

        self.assertEqual(stats, {"imported": 1, "skipped": 1, "unmatched": 0})
        self.assertEqual(list(result.columns), status_columns)
        by_name = result.set_index("企业名称")
        self.assertEqual(
            by_name.at["甲公司", "采购平台网址"],
            "https://confirmed.example.com",
        )
        self.assertEqual(by_name.at["甲公司", "是否验证"], "否")
        self.assertEqual(by_name.at["甲公司", "备注"], "从候选入口导入，待验证")
        self.assertEqual(by_name.at["乙公司", "采购平台网址"], "")
        self.assertEqual(
            by_name.at["丙公司", "采购平台网址"],
            "https://existing.example.com",
        )
        self.assertEqual(by_name.at["丙公司", "备注"], "已有采购平台网址，跳过")
        self.assertEqual(by_name.at["丙公司", "人工负责人"], "C")

    def test_validator_updates_same_fields_without_network(self):
        status_file = self.directory / "enterprise_url_status.xlsx"
        columns = ["人工负责人", *STATUS_COLUMNS]
        status = row_for(
            columns,
            **{
                "人工负责人": "张三",
                "企业名称": "甲公司",
                "采购平台网址": "https://validator.example.com",
                "备注": "人工备注",
            },
        )
        pd.DataFrame([status], columns=columns).to_excel(
            status_file, index=False, engine="openpyxl"
        )
        validation_result = {
            "页面标题": "采购公告平台",
            "HTTP状态码": "200",
            "是否跳转": "否",
            "访问状态": "HTTP 200，未跳转",
            "平台类型": "公开公告平台",
            "是否公开": "是",
            "需要登录": "否",
            "支持搜索": "是",
            "是否可采集": "是",
            "验证结果": "可公开采集",
            "最后检查时间": "2026-07-21 12:00:00",
        }

        with mock.patch.object(enterprise_validator, "create_session", return_value=object()), mock.patch.object(
            enterprise_validator, "validate_url", return_value=validation_result
        ) as validate_mock, mock.patch.object(enterprise_validator.time, "sleep"):
            validate_enterprise_urls(status_file)

        result = read_excel_safe(status_file).fillna("")
        validate_mock.assert_called_once()
        self.assertEqual(list(result.columns), columns + VALIDATION_COLUMNS[:5] + VALIDATION_COLUMNS[8:10])
        for key, value in validation_result.items():
            self.assertEqual(str(result.at[0, key]), value)
        self.assertEqual(result.at[0, "人工负责人"], "张三")
        self.assertEqual(result.at[0, "备注"], "人工备注")

    def test_validator_aborts_when_file_changes_during_validation(self):
        status_file = self.directory / "enterprise_url_status.xlsx"
        status = row_for(
            STATUS_COLUMNS,
            **{
                "企业名称": "甲公司",
                "采购平台网址": "https://validator.example.com",
                "备注": "读取时备注",
            },
        )
        pd.DataFrame([status], columns=STATUS_COLUMNS).to_excel(
            status_file, index=False, engine="openpyxl"
        )

        def external_edit(url, session, checked_time):
            edited = read_excel_safe(status_file)
            edited.at[0, "备注"] = "验证期间人工修改"
            edited.to_excel(status_file, index=False, engine="openpyxl")
            return enterprise_validator.build_empty_url_result(checked_time)

        with mock.patch.object(enterprise_validator, "create_session", return_value=object()), mock.patch.object(
            enterprise_validator, "validate_url", side_effect=external_edit
        ), mock.patch.object(enterprise_validator.time, "sleep"):
            with self.assertRaisesRegex(
                EnterpriseStatusChangedError,
                "changed during validation",
            ):
                validate_enterprise_urls(status_file)

        result = read_excel_safe(status_file).fillna("")
        self.assertEqual(result.at[0, "备注"], "验证期间人工修改")
        self.assertNotIn("页面标题", result.columns)

    def test_status_write_failure_preserves_old_file(self):
        status_file = self.directory / "enterprise_url_status.xlsx"
        status = row_for(STATUS_COLUMNS, **{"企业名称": "甲公司", "备注": "保留"})
        pd.DataFrame([status], columns=STATUS_COLUMNS).to_excel(
            status_file, index=False, engine="openpyxl"
        )
        original_hash = file_hash(status_file)

        with mock.patch("utils.excel_helper.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(ExcelWriteError):
                create_enterprise_url_status_file(status_file)

        self.assertEqual(file_hash(status_file), original_hash)

    def test_candidate_rank_and_export_keep_existing_rules(self):
        candidates_file = self.directory / "enterprise_candidates.xlsx"
        existing = row_for(
            CANDIDATE_COLUMNS,
            **{
                "企业名称": "测试企业",
                "搜索关键词": "测试企业 采购",
                "候选网址": "https://supplier.example.com/srm",
                "网页标题": "供应商采购平台",
                "来源": "测试",
                "是否确认": "是",
                "备注": "人工确认",
            },
        )
        pd.DataFrame([existing], columns=CANDIDATE_COLUMNS).to_excel(
            candidates_file, index=False, engine="openpyxl"
        )

        export_candidates(
            [existing, existing, {**existing, "候选网址": "https://other.example.com"}],
            candidates_file,
        )
        exported = read_excel_safe(candidates_file).fillna("")
        self.assertEqual(len(exported), 2)
        self.assertEqual(exported.iloc[0]["是否确认"], "是")
        self.assertEqual(exported.iloc[0]["备注"], "人工确认")

        expected_scores = [
            score_candidate(row, {}) for _, row in exported.iterrows()
        ]
        rank_candidates(candidates_file)
        ranked = read_excel_safe(candidates_file).fillna("")

        self.assertEqual(list(ranked["候选评分"]), expected_scores)
        self.assertEqual(ranked.iloc[0]["是否确认"], "是")
        self.assertEqual(ranked.iloc[0]["备注"], "人工确认")
        self.assertEqual(list(ranked.columns), CANDIDATE_COLUMNS + ["候选评分", "推荐等级", "建议"])


if __name__ == "__main__":
    unittest.main()
