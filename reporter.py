"""
BidRadar V1.4 daily report.

Read final bid_results.xlsx and generate daily_report.txt.
"""

from datetime import datetime

import pandas as pd


REPORT_FILE = "daily_report.txt"


def generate_daily_report(excel_file, report_file=REPORT_FILE):
    """根据最终导出的 Excel 生成文本日报。"""
    try:
        df = pd.read_excel(excel_file)
    except Exception as error:
        print(f"日报生成失败，无法读取 Excel：{error}")
        return None

    # 兼容空表或旧表：缺少字段时补为空，避免程序报错。
    for column in ["是否新增", "推荐跟进", "价值等级", "招标标题"]:
        if column not in df.columns:
            df[column] = ""

    total_count = len(df)
    new_df = df[df["是否新增"].astype(str) == "是"]
    new_count = len(new_df)
    recommend_count = len(
        df[df["推荐跟进"].astype(str).str.contains("建议", na=False)]
    )
    five_star_count = len(df[df["价值等级"].astype(str) == "★★★★★"])
    four_star_count = len(df[df["价值等级"].astype(str) == "★★★★"])

    lines = [
        "BidRadar 纸箱招标雷达系统 - 数据日报",
        "=" * 40,
        f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"总记录数：{total_count}",
        f"本次新增数量：{new_count}",
        f"推荐跟进数量：{recommend_count}",
        f"五星线索数量：{five_star_count}",
        f"四星线索数量：{four_star_count}",
        "",
        "本次新增的招标标题列表：",
    ]

    if new_count == 0:
        lines.append("本次没有新增招标信息。")
    else:
        for title in new_df["招标标题"].fillna("").astype(str):
            if title.strip():
                lines.append(f"- {title}")

    with open(report_file, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"日报文件：{report_file}")
    return report_file
