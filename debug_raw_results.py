"""
BidRadar V1.7 raw data diagnosis.

This script only exports raw crawler results for debugging.
It does not filter, score, merge history, or change business logic.
"""

import pandas as pd

from crawler import crawl_all_sources


OUTPUT_FILE = "raw_results_debug.xlsx"
TITLE_CHECK_WORDS = [
    "纸箱",
    "包装箱",
    "瓦楞",
    "包装材料",
    "彩箱",
    "纸盒",
]


def main():
    raw_bids = crawl_all_sources()

    rows = []
    for bid in raw_bids:
        raw_text = " ".join(
            [
                str(bid.get("省份", "")),
                str(bid.get("城市", "")),
                str(bid.get("招标标题", "")),
                str(bid.get("采购单位", "")),
                str(bid.get("公告类型", "")),
                str(bid.get("备注", "")),
            ]
        )

        rows.append(
            {
                "信息来源": bid.get("信息来源", ""),
                "搜索关键词": bid.get("搜索关键词", ""),
                "招标标题": bid.get("招标标题", ""),
                "链接": bid.get("链接", ""),
                "发布日期": bid.get("发布日期", ""),
                "原始文本": raw_text,
            }
        )

    df = pd.DataFrame(rows)
    df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print(f"原始数据总数：{len(df)}")
    print()
    print("每个搜索关键词采集数量：")

    if df.empty:
        print("无数据")
    else:
        counts = df["搜索关键词"].fillna("").astype(str).value_counts()
        for keyword, count in counts.items():
            label = keyword if keyword else "普通采集"
            print(f"{label}：{count}")

    print()
    print("标题关键词命中数量：")

    for word in TITLE_CHECK_WORDS:
        if df.empty:
            count = 0
        else:
            count = df["招标标题"].fillna("").astype(str).str.contains(
                word,
                regex=False,
            ).sum()
        print(f"{word}：{count}")

    print()
    print(f"已导出诊断文件：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
