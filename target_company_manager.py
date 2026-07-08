import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import os

import pandas as pd


OUTPUT_FILE = "target_companies.xlsx"

TARGET_COMPANY_COLUMNS = [
    "企业名称",
    "行业",
    "省份",
    "城市",
    "官网",
    "采购平台网址",
    "联系人",
    "电话",
    "邮箱",
    "监控方式",
    "优先级",
    "状态",
    "最后检查时间",
    "备注",
]

DEFAULT_MONITOR_METHOD = "人工+自动"
DEFAULT_PRIORITY = "B"
DEFAULT_STATUS = "待开发"

SEED_COMPANIES = {
    "食品": [
        "伊利",
        "蒙牛",
        "康师傅",
        "统一",
        "达利",
        "旺旺",
        "三只松鼠",
        "良品铺子",
        "洽洽",
        "盼盼",
        "今麦郎",
        "卫龙",
        "白象",
        "农夫山泉",
        "东鹏饮料",
    ],
    "酒类": [
        "五粮液",
        "洋河",
        "古井贡酒",
        "今世缘",
        "迎驾贡酒",
        "口子窖",
        "泸州老窖",
        "青岛啤酒",
        "燕京啤酒",
        "华润啤酒",
    ],
    "家电": [
        "海尔",
        "美的",
        "格力",
        "海信",
        "小熊",
        "创维",
        "长虹",
        "TCL",
        "苏泊尔",
        "九阳",
    ],
    "电子": [
        "立讯精密",
        "歌尔股份",
        "京东方",
        "蓝思科技",
        "闻泰科技",
        "比亚迪电子",
        "欣旺达",
        "德赛电池",
        "领益智造",
        "长电科技",
    ],
    "物流": [
        "京东",
        "顺丰",
        "菜鸟",
        "拼多多",
        "极兔",
    ],
}


def create_or_update_target_companies(output_file=OUTPUT_FILE):
    seed_df = pd.DataFrame(build_seed_rows())

    if os.path.exists(output_file):
        try:
            df = pd.read_excel(output_file)
        except Exception as error:
            print(f"[ERROR] Existing target company file read failed; recreating: {error}")
            df = pd.DataFrame(columns=TARGET_COMPANY_COLUMNS)
    else:
        df = pd.DataFrame(columns=TARGET_COMPANY_COLUMNS)

    df = ensure_columns(df)
    df = merge_seed_companies(df, seed_df)
    df = df[TARGET_COMPANY_COLUMNS]
    df.to_excel(output_file, index=False, engine="openpyxl")

    print(f"总企业数量：{len(df)}")
    print(f"A级：{count_priority(df, 'A')}")
    print(f"B级：{count_priority(df, 'B')}")
    print(f"C级：{count_priority(df, 'C')}")
    print(f"导出文件：{output_file}")

    return output_file


def build_seed_rows():
    rows = []

    for industry, company_names in SEED_COMPANIES.items():
        for company_name in company_names:
            rows.append(
                {
                    "企业名称": company_name,
                    "行业": industry,
                    "省份": "",
                    "城市": "",
                    "官网": "",
                    "采购平台网址": "",
                    "联系人": "",
                    "电话": "",
                    "邮箱": "",
                    "监控方式": DEFAULT_MONITOR_METHOD,
                    "优先级": DEFAULT_PRIORITY,
                    "状态": DEFAULT_STATUS,
                    "最后检查时间": "",
                    "备注": "",
                }
            )

    return rows


def ensure_columns(df):
    for column in TARGET_COMPANY_COLUMNS:
        if column not in df.columns:
            df[column] = default_for_column(column)

    for column in TARGET_COMPANY_COLUMNS:
        df[column] = df[column].astype("object")

    return df


def merge_seed_companies(existing_df, seed_df):
    existing_names = set(
        existing_df["企业名称"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    missing_rows = seed_df[
        ~seed_df["企业名称"].astype(str).str.strip().isin(existing_names)
    ]

    if missing_rows.empty:
        return existing_df

    return pd.concat(
        [existing_df, missing_rows],
        ignore_index=True,
    )


def default_for_column(column):
    if column == "监控方式":
        return DEFAULT_MONITOR_METHOD

    if column == "优先级":
        return DEFAULT_PRIORITY

    if column == "状态":
        return DEFAULT_STATUS

    return ""


def count_priority(df, priority):
    if "优先级" not in df.columns:
        return 0

    return int(
        (
            df["优先级"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            == priority
        ).sum()
    )


if __name__ == "__main__":
    create_or_update_target_companies()
