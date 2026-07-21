import hashlib
import tempfile
import unittest
from datetime import datetime as RealDatetime
from pathlib import Path
from unittest import mock

import pandas as pd

import debug_raw_results
import eia_debug
import reporter
from exporter import EXPORT_COLUMNS
from jianyu_search import RESULT_COLUMNS, export_results
from project_monitor import DEBUG_COLUMNS as PRODUCTION_DEBUG_COLUMNS
from project_monitor import export_raw_debug
from reporter import TextWriteError, generate_daily_report, write_text_safe
from test_sample_run import export_test_results
from utils.excel_helper import ExcelWriteError, read_excel_safe


ROOT = Path(__file__).resolve().parents[1]


class FixedDatetime(RealDatetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 21, 12, 34, 56, tzinfo=tz)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_for(columns, **values):
    row = {column: "" for column in columns}
    row.update(values)
    return row


class DebugOutputSafetyTests(unittest.TestCase):
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
                raise AssertionError(f"Formal output was modified: {path}")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_raw_debug_excel_structure_is_preserved_without_network(self):
        output = self.directory / "raw_results_debug.xlsx"
        raw_bid = {
            "信息来源": "本地测试",
            "搜索关键词": "纸箱",
            "省份": "江苏",
            "城市": "苏州",
            "招标标题": "纸箱采购项目",
            "采购单位": "甲公司",
            "公告类型": "招标公告",
            "发布日期": "2026-07-21",
            "链接": "https://example.com/debug",
            "备注": "测试",
        }

        with mock.patch.object(debug_raw_results, "OUTPUT_FILE", str(output)), mock.patch.object(
            debug_raw_results, "crawl_all_sources", return_value=[raw_bid]
        ) as crawl_mock:
            debug_raw_results.main()

        result = read_excel_safe(output).fillna("")
        crawl_mock.assert_called_once()
        self.assertEqual(
            list(result.columns),
            ["信息来源", "搜索关键词", "招标标题", "链接", "发布日期", "原始文本"],
        )
        self.assertEqual(result.at[0, "招标标题"], "纸箱采购项目")

    def test_raw_jianyu_result_structure_backup_and_failure_protection(self):
        output = self.directory / "raw_jianyu_results.xlsx"
        old = row_for(RESULT_COLUMNS, **{"标题": "旧原始结果", "链接": "old"})
        pd.DataFrame([old], columns=RESULT_COLUMNS).to_excel(
            output, index=False, engine="openpyxl"
        )
        results = [
            row_for(
                RESULT_COLUMNS,
                **{
                    "搜索关键词": "纸箱",
                    "标题": "纸箱采购",
                    "链接": "https://example.com/jianyu",
                    "发布时间": "2026-07-21",
                    "来源": "剑鱼标讯",
                    "采集时间": "2026-07-21 12:00:00",
                },
            )
        ]

        export_results(results, output)
        saved = read_excel_safe(output).fillna("")
        self.assertEqual(list(saved.columns), RESULT_COLUMNS)
        self.assertEqual(saved.at[0, "标题"], "纸箱采购")
        self.assertTrue(list(self.directory.glob("backup/auto/raw_jianyu_results/*.xlsx")))

        protected_hash = file_hash(output)
        with mock.patch("utils.excel_helper.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(ExcelWriteError):
                export_results([{**results[0], "标题": "不能覆盖"}], output)
        self.assertEqual(file_hash(output), protected_hash)

    def test_eia_debug_excel_and_diagnosis_text_keep_structure_and_content(self):
        raw_file = self.directory / "eia_raw_results.xlsx"
        debug_file = self.directory / "eia_raw_debug.xlsx"
        diagnosis_file = self.directory / "eia_diagnosis.txt"
        raw_columns = [*eia_debug.DEBUG_COLUMNS, "人工标签"]
        raw_row = row_for(
            raw_columns,
            **{
                "标题": "江苏食品扩建项目环境影响报告表",
                "链接": "https://example.com/eia",
                "来源": "本地测试",
                "发布日期": "2026-07-21",
                "搜索关键词": "环评",
                "原始文本": "江苏苏州食品生产基地扩建环境影响报告表",
                "省份": "江苏",
                "城市": "苏州",
                "人工标签": "保留",
            },
        )
        pd.DataFrame([raw_row], columns=raw_columns).to_excel(
            raw_file, index=False, engine="openpyxl"
        )
        pd.DataFrame([{"旧": "旧调试"}]).to_excel(
            debug_file, index=False, engine="openpyxl"
        )
        diagnosis_file.write_text("旧诊断", encoding="utf-8")

        with mock.patch.object(eia_debug, "RAW_FILE", str(raw_file)), mock.patch.object(
            eia_debug, "DEBUG_FILE", str(debug_file)
        ), mock.patch.object(
            eia_debug, "DIAGNOSIS_FILE", str(diagnosis_file)
        ), mock.patch.object(eia_debug, "datetime", FixedDatetime):
            result = eia_debug.run_eia_debug()

        debug_result = read_excel_safe(debug_file).fillna("")
        with mock.patch.object(eia_debug, "datetime", FixedDatetime):
            expected_lines = eia_debug.build_diagnosis_lines(
                result["stats"],
                result["eia_counts"],
                result["industry_counts"],
                result["region_counts"],
                result["sample_titles"],
            )
        self.assertEqual(list(debug_result.columns), raw_columns)
        self.assertEqual(debug_result.at[0, "人工标签"], "保留")
        self.assertEqual(
            diagnosis_file.read_text(encoding="utf-8"),
            "\n".join(expected_lines),
        )
        self.assertTrue(list(self.directory.glob("backup/auto/eia_raw_debug/*.xlsx")))
        self.assertTrue(list(self.directory.glob("backup/auto/eia_diagnosis/*.txt")))

    def test_daily_report_text_format_is_unchanged(self):
        excel_file = self.directory / "bid_results.xlsx"
        report_file = self.directory / "daily_report.txt"
        report_file.write_text("旧日报", encoding="utf-8")
        rows = [
            {
                "是否新增": "是",
                "推荐跟进": "建议重点跟进",
                "价值等级": "★★★★★",
                "招标标题": "甲公司纸箱项目",
            },
            {
                "是否新增": "否",
                "推荐跟进": "暂不优先",
                "价值等级": "★★★★",
                "招标标题": "历史项目",
            },
        ]
        pd.DataFrame(rows).to_excel(excel_file, index=False, engine="openpyxl")
        expected = "\n".join(
            [
                "BidRadar 纸箱招标雷达系统 - 数据日报",
                "=" * 40,
                "运行时间：2026-07-21 12:34:56",
                "总记录数：2",
                "本次新增数量：1",
                "推荐跟进数量：1",
                "五星线索数量：1",
                "四星线索数量：1",
                "",
                "本次新增的招标标题列表：",
                "- 甲公司纸箱项目",
            ]
        )

        with mock.patch.object(reporter, "datetime", FixedDatetime):
            generate_daily_report(excel_file, report_file)

        self.assertEqual(report_file.read_text(encoding="utf-8"), expected)
        self.assertTrue(list(self.directory.glob("backup/auto/daily_report/*.txt")))

    def test_text_write_failure_preserves_old_file(self):
        output = self.directory / "protected.txt"
        output.write_text("必须保留的旧内容", encoding="utf-8")
        original_hash = file_hash(output)

        with mock.patch.object(reporter.os, "replace", side_effect=OSError("blocked")):
            with self.assertRaises(TextWriteError):
                write_text_safe("新内容", output)

        self.assertEqual(file_hash(output), original_hash)

    def test_production_debug_and_sample_outputs_use_safe_excel_writes(self):
        production_debug = self.directory / "production_raw_debug.xlsx"
        sample_output = self.directory / "test_bid_results.xlsx"
        item = {
            "title": "苏州食品生产基地项目",
            "link": "https://example.com/project",
            "text": "江苏苏州食品生产基地",
            "query": "生产基地",
            "source": {"name": "本地测试", "province": "江苏"},
        }

        export_raw_debug([item], production_debug)
        production = read_excel_safe(production_debug).fillna("")
        self.assertEqual(list(production.columns), PRODUCTION_DEBUG_COLUMNS)

        sample_record = row_for(
            EXPORT_COLUMNS,
            **{
                "招标标题": "测试纸箱项目",
                "采购单位": "甲公司",
                "发布日期": "2026-07-21",
                "链接": "https://example.com/sample",
            },
        )
        export_test_results([sample_record], sample_output)
        sample = read_excel_safe(sample_output).fillna("")
        self.assertEqual(list(sample.columns), EXPORT_COLUMNS)
        self.assertEqual(sample.at[0, "是否新增"], "是")


if __name__ == "__main__":
    unittest.main()
