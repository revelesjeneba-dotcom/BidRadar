import importlib.util
import socket
import unittest
from collections import Counter

from industry_filter import is_carton_related
from sample_data import get_sample_bids
from scoring import get_level, get_priority, get_recommend, score_bid


DEPENDENCIES_AVAILABLE = all(
    importlib.util.find_spec(package) is not None
    for package in ("pandas", "openpyxl", "requests", "bs4")
)


class BusinessBaselineTests(unittest.TestCase):
    def test_sample_fixture_and_pure_business_rules(self):
        samples = get_sample_bids()
        self.assertEqual(len(samples), 7)
        self.assertTrue(is_carton_related(samples[0]["招标标题"]))
        self.assertFalse(is_carton_related("南京办公设备维保服务采购"))

    def test_scoring_boundaries_are_frozen(self):
        expected = {
            0: ("★", "观察", "暂不优先"),
            30: ("★★", "低", "可作为备选"),
            50: ("★★★", "中", "建议跟进"),
            70: ("★★★★", "高", "建议重点跟进"),
            90: ("★★★★★", "最高", "建议重点跟进"),
        }
        for score, values in expected.items():
            with self.subTest(score=score):
                self.assertEqual((get_level(score), get_priority(score), get_recommend(score)), values)

    @unittest.skipUnless(DEPENDENCIES_AVAILABLE, "project runtime dependencies are not installed")
    def test_sample_pipeline_baseline_without_network_or_file_writes(self):
        original_socket = socket.socket
        original_create_connection = socket.create_connection

        class BlockedSocket(socket.socket):
            def connect(self, address):
                raise AssertionError(f"Unexpected network access: {address}")

            def connect_ex(self, address):
                raise AssertionError(f"Unexpected network access: {address}")

        def blocked_create_connection(address, *args, **kwargs):
            raise AssertionError(f"Unexpected network access: {address}")

        socket.socket = BlockedSocket
        socket.create_connection = blocked_create_connection
        try:
            from main import build_results

            results = build_results(get_sample_bids())
        finally:
            socket.socket = original_socket
            socket.create_connection = original_create_connection

        self.assertEqual(len(results), 5)
        self.assertEqual(len({row["唯一ID"] for row in results}), 5)
        self.assertEqual(
            Counter(row["价值等级"] for row in results),
            Counter({"★": 2, "★★": 1, "★★★": 1, "★★★★★": 1}),
        )
        self.assertEqual(
            Counter(row["跟进优先级"] for row in results),
            Counter({"观察": 2, "低": 1, "中": 1, "最高": 1}),
        )

        expected_columns = [
            "唯一ID", "是否新增", "采集日期", "搜索关键词", "省份",
            "地区识别置信度", "城市", "招标标题", "采购单位", "公告类型",
            "发布日期", "截止日期", "预算金额", "信息来源", "链接",
            "匹配关键词", "价值分数", "价值等级", "推荐跟进", "跟进优先级",
            "跟进状态", "备注",
        ]
        self.assertTrue(all(list(row) == expected_columns for row in results))


if __name__ == "__main__":
    unittest.main()
