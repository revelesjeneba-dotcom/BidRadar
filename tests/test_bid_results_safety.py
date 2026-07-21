import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

import exporter
from exporter import EXPORT_COLUMNS, export_to_excel, make_unique_id
from jianyu_importer import RAW_COLUMNS, import_jianyu_results
from manual_import import MANUAL_COLUMNS, import_manual_bids
from paths import BID_RESULTS
from utils.excel_helper import ExcelReadError, ExcelWriteError, read_excel_safe


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def complete_record(**overrides):
    record = {column: "" for column in EXPORT_COLUMNS}
    record.update(
        {
            "采集日期": "2026-07-21",
            "省份": "江苏",
            "城市": "苏州",
            "招标标题": "纸箱采购项目",
            "采购单位": "测试企业",
            "发布日期": "2026-07-20",
            "链接": "https://example.com/bid/1",
            "跟进状态": "待跟进",
        }
    )
    record.update(overrides)
    record["唯一ID"] = record.get("唯一ID") or make_unique_id(record)
    return record


def legacy_export_result(records, history_df):
    """V6.5.5 exporter transformation retained as an independent baseline."""
    current_df = pd.DataFrame(records)
    for column in EXPORT_COLUMNS:
        if column not in current_df.columns:
            current_df[column] = ""

    if not current_df.empty:
        current_df["唯一ID"] = current_df.apply(
            lambda row: make_unique_id(row.to_dict()), axis=1
        )
        current_df = current_df.drop_duplicates(subset=["唯一ID"], keep="first")

    history_df = history_df.copy()
    for column in EXPORT_COLUMNS:
        if column not in history_df.columns:
            history_df[column] = ""

    history_ids = set()
    if not history_df.empty:
        history_df["唯一ID"] = history_df.apply(
            lambda row: exporter._existing_or_new_unique_id(row), axis=1
        )
        history_df = history_df.drop_duplicates(subset=["唯一ID"], keep="first")
        history_df["是否新增"] = "否"
        history_ids = set(history_df["唯一ID"].astype(str))

    if not current_df.empty:
        current_df = current_df[
            ~current_df["唯一ID"].astype(str).isin(history_ids)
        ]
        current_df["是否新增"] = "是"

    combined_df = pd.concat([history_df, current_df], ignore_index=True)
    for column in EXPORT_COLUMNS:
        if column not in combined_df.columns:
            combined_df[column] = ""
    return combined_df[EXPORT_COLUMNS]


class BidResultsSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formal_hash = file_hash(BID_RESULTS)

    @classmethod
    def tearDownClass(cls):
        if file_hash(BID_RESULTS) != cls.formal_hash:
            raise AssertionError("Formal bid_results.xlsx was modified by tests")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_exporter_matches_legacy_result_columns_order_and_unique_ids(self):
        output = self.directory / "bid_results.xlsx"
        history = pd.DataFrame(
            [complete_record(招标标题="历史纸箱采购", 链接="https://example.com/old")]
        )[EXPORT_COLUMNS]
        history.to_excel(output, index=False, engine="openpyxl")
        records = [
            complete_record(招标标题="历史重复", 链接="https://example.com/old"),
            complete_record(招标标题="新纸箱采购", 链接="https://example.com/new"),
            complete_record(招标标题="新纸箱采购重复", 链接="https://example.com/new"),
        ]
        expected = legacy_export_result(records, history)

        export_to_excel(records, output)
        actual = read_excel_safe(output).fillna("")

        pd.testing.assert_frame_equal(
            actual.reset_index(drop=True),
            expected.fillna("").reset_index(drop=True),
            check_dtype=False,
        )
        self.assertEqual(list(actual.columns), EXPORT_COLUMNS)
        self.assertEqual(
            set(actual["唯一ID"].astype(str)),
            set(expected["唯一ID"].astype(str)),
        )
        self.assertEqual(actual["唯一ID"].nunique(), len(actual))
        self.assertTrue(list(self.directory.glob("backup/auto/bid_results/*.xlsx")))

    def test_exporter_creates_missing_result_file(self):
        output = self.directory / "new_bid_results.xlsx"

        export_to_excel([complete_record()], str(output))

        self.assertTrue(output.is_file())
        self.assertEqual(list(read_excel_safe(output).columns), EXPORT_COLUMNS)

    def test_damaged_history_aborts_without_overwriting_it(self):
        output = self.directory / "damaged.xlsx"
        output.write_bytes(b"damaged historical workbook")
        original_hash = file_hash(output)

        with self.assertRaises(ExcelReadError):
            export_to_excel([complete_record()], output)

        self.assertEqual(file_hash(output), original_hash)

    def test_integrated_write_failure_preserves_existing_result(self):
        output = self.directory / "protected.xlsx"
        history = pd.DataFrame([complete_record()])[EXPORT_COLUMNS]
        history.to_excel(output, index=False, engine="openpyxl")
        original_hash = file_hash(output)

        with mock.patch("utils.excel_helper.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(ExcelWriteError):
                export_to_excel(
                    [complete_record(链接="https://example.com/new")],
                    output,
                )

        self.assertEqual(file_hash(output), original_hash)

    def test_manual_import_uses_safe_result_write_without_rule_changes(self):
        manual_file = self.directory / "manual.xlsx"
        output = self.directory / "manual_bid_results.xlsx"
        manual_row = {column: "" for column in MANUAL_COLUMNS}
        manual_row.update(
            {
                "标题": "年度纸箱采购",
                "链接": "https://example.com/manual",
                "发布日期": "2026-07-20",
                "采购单位": "人工企业",
                "省份": "江苏",
            }
        )
        pd.DataFrame([manual_row], columns=MANUAL_COLUMNS).to_excel(
            manual_file, index=False, engine="openpyxl"
        )

        stats = import_manual_bids(manual_file, output)
        result = read_excel_safe(output).fillna("")

        self.assertEqual(stats["imported"], 1)
        self.assertEqual(list(result.columns), EXPORT_COLUMNS)
        self.assertEqual(result.at[0, "唯一ID"], "link:https://example.com/manual")
        self.assertEqual(result.at[0, "信息来源"], "人工导入")

    def test_jianyu_import_uses_safe_result_write_without_rule_changes(self):
        raw_file = self.directory / "raw_jianyu.xlsx"
        output = self.directory / "jianyu_bid_results.xlsx"
        raw_row = {column: "" for column in RAW_COLUMNS}
        raw_row.update(
            {
                "搜索关键词": "纸箱",
                "标题": "纸箱供应商招募",
                "链接": "https://example.com/jianyu",
                "发布时间": "2026-07-20",
                "来源": "剑鱼标讯",
            }
        )
        pd.DataFrame([raw_row], columns=RAW_COLUMNS).to_excel(
            raw_file, index=False, engine="openpyxl"
        )

        stats = import_jianyu_results(raw_file, output)
        result = read_excel_safe(output).fillna("")

        self.assertEqual(stats["imported"], 1)
        self.assertEqual(list(result.columns), EXPORT_COLUMNS)
        self.assertEqual(result.at[0, "唯一ID"], "link:https://example.com/jianyu")
        self.assertEqual(result.at[0, "信息来源"], "剑鱼标讯")


if __name__ == "__main__":
    unittest.main()
