import pandas as pd
import os

from config import PROVINCE_CONFIDENCE_COLUMN

EXPORT_COLUMNS = [
    "唯一ID",
    "是否新增",
    "采集日期",
    "搜索关键词",
    "省份",
    PROVINCE_CONFIDENCE_COLUMN,
    "城市",
    "招标标题",
    "采购单位",
    "公告类型",
    "发布日期",
    "截止日期",
    "预算金额",
    "信息来源",
    "链接",
    "匹配关键词",
    "价值分数",
    "价值等级",
    "推荐跟进",
    "跟进优先级",
    "跟进状态",
    "备注",
]


def make_unique_id(record):
    """
    生成去重用唯一 ID。

    优先使用链接；没有链接时使用 招标标题 + 采购单位 + 发布日期。
    """
    link = str(record.get("链接", "")).strip()

    if link:
        return "link:" + link

    title = str(record.get("招标标题", "")).strip()
    buyer = str(record.get("采购单位", "")).strip()
    publish_date = str(record.get("发布日期", "")).strip()

    return f"text:{title}|{buyer}|{publish_date}"


def export_to_excel(records, output_file):
    current_df = pd.DataFrame(records)

    for column in EXPORT_COLUMNS:
        if column not in current_df.columns:
            current_df[column] = ""

    if not current_df.empty:
        current_df["唯一ID"] = current_df.apply(
            lambda row: make_unique_id(row.to_dict()),
            axis=1,
        )
        current_df = current_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )

    history_df = _read_history(output_file)
    history_ids = set()

    if not history_df.empty:
        history_df["唯一ID"] = history_df.apply(
            lambda row: _existing_or_new_unique_id(row),
            axis=1,
        )
        history_df = history_df.drop_duplicates(
            subset=["唯一ID"],
            keep="first",
        )
        history_df["是否新增"] = "否"
        history_ids = set(history_df["唯一ID"].astype(str))

    if not current_df.empty:
        current_df = current_df[
            ~current_df["唯一ID"].astype(str).isin(history_ids)
        ]
        current_df["是否新增"] = "是"

    combined_df = pd.concat(
        [
            history_df,
            current_df,
        ],
        ignore_index=True,
    )

    for column in EXPORT_COLUMNS:
        if column not in combined_df.columns:
            combined_df[column] = ""

    combined_df = combined_df[EXPORT_COLUMNS]
    combined_df.to_excel(output_file, index=False, engine="openpyxl")

    return output_file


def _read_history(output_file):
    if not os.path.exists(output_file):
        return pd.DataFrame(columns=EXPORT_COLUMNS)

    try:
        history_df = pd.read_excel(output_file)
    except Exception as error:
        print(f"历史结果读取失败，将重新生成：{error}")
        return pd.DataFrame(columns=EXPORT_COLUMNS)

    for column in EXPORT_COLUMNS:
        if column not in history_df.columns:
            history_df[column] = ""

    return history_df


def _existing_or_new_unique_id(row):
    unique_id = str(row.get("唯一ID", "")).strip()

    if unique_id and unique_id.lower() != "nan":
        return unique_id

    return make_unique_id(row.to_dict())
