import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from utils.excel_helper import (
    ExcelReadError,
    ExcelValidationError,
    ExcelWriteError,
    backup_excel,
    build_excel_summary,
    ensure_columns,
    read_excel_safe,
    validate_columns,
    write_excel_safe,
)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ExcelHelperTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.frame = pd.DataFrame(
            [
                {"企业名称": "甲公司", "状态": "待开发"},
                {"企业名称": "乙公司", "状态": "已联系"},
            ]
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_writes_new_file_and_accepts_string_path(self):
        destination = self.directory / "new.xlsx"

        result = write_excel_safe(self.frame, str(destination))

        self.assertTrue(destination.is_file())
        self.assertIsNone(result["backup_path"])
        self.assertEqual(result["summary"]["row_count"], 2)
        pd.testing.assert_frame_equal(read_excel_safe(destination), self.frame)

    def test_existing_file_is_backed_up_before_replacement(self):
        destination = self.directory / "existing.xlsx"
        backup_directory = self.directory / "backups"
        original = pd.DataFrame([{"企业名称": "原公司", "状态": "保留"}])
        original.to_excel(destination, index=False, engine="openpyxl")
        original_hash = file_hash(destination)

        result = write_excel_safe(
            self.frame,
            destination,
            backup_dir=backup_directory,
        )

        backup_path = result["backup_path"]
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.is_file())
        self.assertEqual(file_hash(backup_path), original_hash)
        pd.testing.assert_frame_equal(read_excel_safe(destination), self.frame)

    def test_backup_excel_supports_path_and_string(self):
        destination = self.directory / "source.xlsx"
        self.frame.to_excel(destination, index=False, engine="openpyxl")

        backup_path = backup_excel(str(destination), self.directory / "copies")

        self.assertTrue(backup_path.is_file())
        self.assertEqual(file_hash(backup_path), file_hash(destination))

    def test_damaged_excel_read_raises_instead_of_returning_empty_data(self):
        damaged = self.directory / "damaged.xlsx"
        damaged.write_bytes(b"not an Excel workbook")

        with self.assertRaises(ExcelReadError):
            read_excel_safe(damaged)

    def test_missing_required_columns_are_detected(self):
        with self.assertRaises(ExcelValidationError):
            validate_columns(self.frame, ["企业名称", "缺少字段"])

        workbook = self.directory / "columns.xlsx"
        self.frame.to_excel(workbook, index=False, engine="openpyxl")
        with self.assertRaises(ExcelValidationError):
            read_excel_safe(workbook, required_columns=["缺少字段"])

    def test_failed_write_preserves_original_file(self):
        destination = self.directory / "protected.xlsx"
        self.frame.to_excel(destination, index=False, engine="openpyxl")
        original_hash = file_hash(destination)

        with mock.patch("utils.excel_helper.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(ExcelWriteError):
                write_excel_safe(
                    pd.DataFrame([{"企业名称": "新公司", "状态": "新状态"}]),
                    destination,
                    backup_dir=self.directory / "backups",
                )

        self.assertEqual(file_hash(destination), original_hash)
        pd.testing.assert_frame_equal(read_excel_safe(destination), self.frame)

    def test_written_structure_and_column_order_are_preserved(self):
        destination = self.directory / "ordered.xlsx"
        ordered = pd.DataFrame([{"第三列": 3, "第一列": 1, "第二列": 2}])

        result = write_excel_safe(
            ordered,
            destination,
            required_columns=["第三列", "第一列", "第二列"],
        )
        saved = read_excel_safe(destination)

        self.assertEqual(list(saved.columns), ["第三列", "第一列", "第二列"])
        self.assertEqual(result["summary"], build_excel_summary(saved, destination))

    def test_ensure_columns_orders_requested_columns_and_preserves_extras(self):
        source = pd.DataFrame([{"额外列": "保留", "第二列": "二"}])

        result = ensure_columns(source, ["第一列", "第二列"])

        self.assertEqual(list(result.columns), ["第一列", "第二列", "额外列"])
        self.assertEqual(result.at[0, "第一列"], "")
        self.assertEqual(result.at[0, "额外列"], "保留")
        self.assertEqual(list(source.columns), ["额外列", "第二列"])


if __name__ == "__main__":
    unittest.main()
