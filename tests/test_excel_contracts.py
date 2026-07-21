import ast
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
XML_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


WORKBOOK_CONTRACTS = {
    "bid_results.xlsx": [
        "唯一ID", "是否新增", "采集日期", "搜索关键词", "省份",
        "地区识别置信度", "城市", "招标标题", "采购单位", "公告类型",
        "发布日期", "截止日期", "预算金额", "信息来源", "链接",
        "匹配关键词", "价值分数", "价值等级", "推荐跟进", "跟进优先级",
        "跟进状态", "备注",
    ],
    "customer_pool.xlsx": [
        "企业名称", "行业", "来源", "招标标题", "省份", "城市",
        "首次发现日期", "最后跟进日期", "开发状态", "优先级", "价值分数",
        "官网", "电话", "邮箱", "采购平台网址", "备注", "首次联系日期",
        "下次跟进日期", "跟进次数", "跟进状态", "最近跟进记录",
    ],
    "followup_tasks.xlsx": [
        "企业名称", "行业", "电话", "邮箱", "开发状态", "最后跟进日期",
        "未跟进天数", "提醒等级", "建议动作", "备注",
    ],
    "enterprise_url_status.xlsx": [
        "企业名称", "行业", "官网", "采购平台网址", "优先级", "是否公开",
        "需要登录", "支持搜索", "是否验证", "最后检查时间", "备注",
        "页面标题", "访问状态", "平台类型", "是否可采集", "验证结果",
        "HTTP状态码", "是否跳转",
    ],
    "high_value_leads.xlsx": [
        "推荐等级", "招标标题", "采购单位", "省份", "城市", "价值分数",
        "推荐跟进", "跟进优先级", "链接", "推荐动作",
    ],
    "target_companies.xlsx": [
        "企业名称", "行业", "省份", "城市", "官网", "采购平台网址", "联系人",
        "电话", "邮箱", "监控方式", "优先级", "状态", "最后检查时间", "备注",
    ],
    "customer_contact_candidates.xlsx": [
        "企业名称", "搜索关键词", "候选标题", "候选网址", "候选电话", "候选邮箱",
        "来源", "是否确认", "备注",
    ],
}


SOURCE_CONTRACTS = {
    ("exporter.py", "EXPORT_COLUMNS"): WORKBOOK_CONTRACTS["bid_results.xlsx"],
    ("followup_manager.py", "TASK_COLUMNS"): WORKBOOK_CONTRACTS["followup_tasks.xlsx"],
    ("enterprise_source_manager.py", "STATUS_COLUMNS"): WORKBOOK_CONTRACTS["enterprise_url_status.xlsx"][:11],
    ("high_value_filter.py", "OUTPUT_COLUMNS"): WORKBOOK_CONTRACTS["high_value_leads.xlsx"],
    ("target_company_manager.py", "TARGET_COMPANY_COLUMNS"): WORKBOOK_CONTRACTS["target_companies.xlsx"],
    ("contact_finder.py", "CANDIDATE_COLUMNS"): WORKBOOK_CONTRACTS["customer_contact_candidates.xlsx"],
}

SYMBOL_VALUES = {
    "PROVINCE_CONFIDENCE_COLUMN": "地区识别置信度",
}


def read_list_constant(file_name, constant_name):
    tree = ast.parse((ROOT / file_name).read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == constant_name for target in node.targets):
            values = []
            if not isinstance(node.value, (ast.List, ast.Tuple)):
                raise AssertionError(f"{constant_name} in {file_name} is not a list")
            for item in node.value.elts:
                if isinstance(item, ast.Constant):
                    values.append(item.value)
                elif isinstance(item, ast.Name) and item.id in SYMBOL_VALUES:
                    values.append(SYMBOL_VALUES[item.id])
                else:
                    raise AssertionError(
                        f"Unsupported value in {file_name}:{constant_name}: {ast.dump(item)}"
                    )
            return values
    raise AssertionError(f"Missing {constant_name} in {file_name}")


def read_xlsx_headers(path):
    """Read the first worksheet header using only the Python standard library."""
    with zipfile.ZipFile(path) as archive:
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("x:si", XML_NS):
                shared_strings.append("".join(node.text or "" for node in item.iterfind(".//x:t", XML_NS)))

        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        row = sheet.find(".//x:sheetData/x:row", XML_NS)
        if row is None:
            return []

        headers = []
        for cell in row.findall("x:c", XML_NS):
            value = cell.find("x:v", XML_NS)
            if cell.get("t") == "inlineStr":
                headers.append("".join(node.text or "" for node in cell.iterfind(".//x:t", XML_NS)))
            elif value is None:
                headers.append("")
            elif cell.get("t") == "s":
                headers.append(shared_strings[int(value.text)])
            else:
                headers.append(value.text or "")
        return headers


class ExcelContractTests(unittest.TestCase):
    def test_declared_source_columns_match_frozen_contracts(self):
        for (file_name, constant_name), expected in SOURCE_CONTRACTS.items():
            with self.subTest(file=file_name, constant=constant_name):
                self.assertEqual(read_list_constant(file_name, constant_name), expected)

    def test_existing_workbook_headers_match_frozen_contracts(self):
        for file_name, expected in WORKBOOK_CONTRACTS.items():
            with self.subTest(workbook=file_name):
                path = ROOT / file_name
                self.assertTrue(path.is_file(), f"Missing workbook: {file_name}")
                self.assertEqual(read_xlsx_headers(path), expected)


if __name__ == "__main__":
    unittest.main()
