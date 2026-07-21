import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

import contact_finder
import eia_monitor
import expansion_monitor
import project_monitor
import target_company_manager
from high_value_filter import OUTPUT_COLUMNS as HIGH_VALUE_COLUMNS
from high_value_filter import export_high_value_leads
from target_company_manager import TARGET_COMPANY_COLUMNS
from utils.excel_helper import ExcelReadError, ExcelWriteError, read_excel_safe


ROOT = Path(__file__).resolve().parents[1]


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_for(columns, **values):
    row = {column: "" for column in columns}
    row.update(values)
    return row


class ProjectOutputsSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formal_hashes = {
            path: file_hash(path) for path in ROOT.glob("*.xlsx")
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

    def test_target_companies_preserve_history_manual_fields_and_column_order(self):
        output = self.directory / "target_companies.xlsx"
        columns = ["人工负责人", *TARGET_COMPANY_COLUMNS]
        existing = row_for(
            columns,
            **{
                "人工负责人": "张三",
                "企业名称": "甲公司",
                "行业": "食品",
                "官网": "https://manual.example.com",
                "优先级": "A",
                "状态": "跟进中",
                "备注": "人工备注",
            },
        )
        seed = row_for(
            TARGET_COMPANY_COLUMNS,
            **{
                "企业名称": "乙公司",
                "行业": "电子",
                "监控方式": "人工+自动",
                "优先级": "B",
                "状态": "待开发",
            },
        )
        pd.DataFrame([existing], columns=columns).to_excel(
            output, index=False, engine="openpyxl"
        )

        with mock.patch.object(
            target_company_manager,
            "build_seed_rows",
            return_value=[seed],
        ):
            target_company_manager.create_or_update_target_companies(output)

        result = read_excel_safe(output).fillna("")
        self.assertEqual(list(result.columns), columns)
        self.assertEqual(set(result["企业名称"]), {"甲公司", "乙公司"})
        saved = result[result["企业名称"] == "甲公司"].iloc[0]
        self.assertEqual(saved["人工负责人"], "张三")
        self.assertEqual(saved["官网"], "https://manual.example.com")
        self.assertEqual(saved["状态"], "跟进中")
        self.assertEqual(saved["备注"], "人工备注")
        self.assertTrue(list(self.directory.glob("backup/auto/target_companies/*.xlsx")))

    def test_high_value_recalculation_keeps_result_and_structure(self):
        input_file = self.directory / "bid_results.xlsx"
        output_file = self.directory / "high_value_leads.xlsx"
        input_rows = [
            {
                "招标标题": "年度纸箱采购",
                "采购单位": "甲集团有限公司",
                "省份": "江苏",
                "城市": "苏州",
                "价值分数": 80,
                "价值等级": "★★★★",
                "推荐跟进": "建议重点跟进",
                "跟进优先级": "高",
                "链接": "https://example.com/high",
                "公告类型": "年度采购",
                "备注": "",
                "匹配关键词": "纸箱",
            },
            {
                "招标标题": "普通办公采购",
                "采购单位": "乙公司",
                "价值分数": 10,
            },
        ]
        pd.DataFrame(input_rows).to_excel(input_file, index=False, engine="openpyxl")
        pd.DataFrame([row_for(HIGH_VALUE_COLUMNS, **{"招标标题": "旧结果"})]).to_excel(
            output_file, index=False, engine="openpyxl"
        )

        stats = export_high_value_leads(input_file, output_file)
        result = read_excel_safe(output_file).fillna("")

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["high_value"], 1)
        self.assertEqual(stats["immediate"], 1)
        self.assertEqual(list(result.columns), HIGH_VALUE_COLUMNS)
        self.assertEqual(result.at[0, "招标标题"], "年度纸箱采购")
        self.assertEqual(result.at[0, "推荐等级"], "四星线索")
        self.assertEqual(result.at[0, "推荐动作"], "建议立即开发")
        self.assertTrue(list(self.directory.glob("backup/auto/high_value_leads/*.xlsx")))

    def test_recalculable_output_failure_preserves_old_file(self):
        input_file = self.directory / "bid_results.xlsx"
        output_file = self.directory / "high_value_leads.xlsx"
        pd.DataFrame([{"招标标题": "年度采购", "采购单位": "甲公司"}]).to_excel(
            input_file, index=False, engine="openpyxl"
        )
        pd.DataFrame([row_for(HIGH_VALUE_COLUMNS, **{"招标标题": "旧结果"})]).to_excel(
            output_file, index=False, engine="openpyxl"
        )
        original_hash = file_hash(output_file)

        with mock.patch("utils.excel_helper.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(ExcelWriteError):
                export_high_value_leads(input_file, output_file)

        self.assertEqual(file_hash(output_file), original_hash)

    def test_contact_candidates_recalculation_is_safe_and_offline(self):
        customer_file = self.directory / "customer_pool.xlsx"
        output_file = self.directory / "customer_contact_candidates.xlsx"
        customer = {
            "企业名称": "甲公司",
            "官网": "",
            "电话": "",
            "邮箱": "",
            "采购平台网址": "",
        }
        pd.DataFrame([customer]).to_excel(
            customer_file, index=False, engine="openpyxl"
        )
        pd.DataFrame(
            [row_for(contact_finder.CANDIDATE_COLUMNS, **{"企业名称": "旧结果"})]
        ).to_excel(output_file, index=False, engine="openpyxl")
        search_result = {
            "title": "甲公司官网",
            "url": "https://a.example.com",
            "phone": "025-12345678",
            "email": "contact@example.com",
            "source": "本地测试",
        }

        with mock.patch.object(contact_finder, "create_session", return_value=object()), mock.patch.object(
            contact_finder, "build_search_keywords", return_value=["甲公司 官网"]
        ), mock.patch.object(
            contact_finder, "search_public_web", return_value=[search_result]
        ) as search_mock, mock.patch.object(contact_finder.time, "sleep"):
            stats = contact_finder.find_contact_candidates(customer_file, output_file)

        result = read_excel_safe(output_file).fillna("")
        search_mock.assert_called_once()
        self.assertEqual(stats["customers"], 1)
        self.assertEqual(stats["candidates"], 1)
        self.assertEqual(list(result.columns), contact_finder.CANDIDATE_COLUMNS)
        self.assertEqual(result.at[0, "候选网址"], "https://a.example.com")
        self.assertEqual(result.at[0, "候选电话"], "025-12345678")
        self.assertEqual(result.at[0, "是否确认"], "否")
        self.assertEqual(result.at[0, "备注"], "待人工确认")

    def test_project_histories_keep_columns_ids_and_rows_without_network(self):
        cases = [
            (project_monitor, "run_project_monitor", "production_projects.xlsx"),
            (eia_monitor, "run_eia_monitor", "eia_projects.xlsx"),
            (expansion_monitor, "run_expansion_monitor", "expansion_projects.xlsx"),
        ]
        for module, function_name, file_name in cases:
            with self.subTest(module=module.__name__):
                output = self.directory / file_name
                unique_id = f"test:{module.__name__}"
                history = row_for(
                    module.OUTPUT_COLUMNS,
                    **{
                        "唯一ID": unique_id,
                        "企业名称": "历史企业",
                        "项目名称": "历史项目",
                        "链接": "https://example.com/history",
                        "价值分数": 80,
                        "推荐等级": "A级",
                        "推荐动作": "保持",
                    },
                )
                pd.DataFrame([history], columns=module.OUTPUT_COLUMNS).to_excel(
                    output, index=False, engine="openpyxl"
                )

                run = getattr(module, function_name)
                if module is project_monitor:
                    debug = self.directory / "production_raw_debug.xlsx"
                    stats = run(sources=[], output_file=output, debug_file=debug)
                    self.assertEqual(list(read_excel_safe(debug).columns), module.DEBUG_COLUMNS)
                else:
                    stats = run(sources=[], output_file=output)

                result = read_excel_safe(output).fillna("")
                self.assertEqual(stats["raw_count"], 0)
                self.assertEqual(stats["new_count"], 0)
                self.assertEqual(list(result.columns), module.OUTPUT_COLUMNS)
                self.assertEqual(len(result), 1)
                self.assertEqual(set(result["唯一ID"]), {unique_id})
                self.assertEqual(result.at[0, "企业名称"], "历史企业")
                if "价值分数" in module.OUTPUT_COLUMNS:
                    self.assertEqual(result.at[0, "价值分数"], 80)
                self.assertEqual(result.at[0, "推荐等级"], "A级")
                self.assertEqual(result.at[0, "推荐动作"], "保持")
                self.assertTrue(
                    list(self.directory.glob(f"backup/auto/{output.stem}/*.xlsx"))
                )

    def test_damaged_project_histories_stop_instead_of_rebuilding(self):
        for module in (project_monitor, eia_monitor, expansion_monitor):
            with self.subTest(module=module.__name__):
                output = self.directory / f"damaged_{module.__name__}.xlsx"
                output.write_bytes(b"damaged project history")
                original_hash = file_hash(output)

                with self.assertRaises(ExcelReadError):
                    module.read_history(output)

                self.assertEqual(file_hash(output), original_hash)


if __name__ == "__main__":
    unittest.main()
