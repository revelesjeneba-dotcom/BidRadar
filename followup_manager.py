import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from datetime import date, datetime
import os

import pandas as pd


CUSTOMER_POOL_FILE = "customer_pool.xlsx"
OUTPUT_FILE = "followup_tasks.xlsx"

FOLLOWUP_COLUMNS = [
    "首次联系日期",
    "最后跟进日期",
    "下次跟进日期",
    "跟进次数",
    "跟进状态",
    "最近跟进记录",
]

TASK_COLUMNS = [
    "企业名称",
    "行业",
    "电话",
    "邮箱",
    "开发状态",
    "最后跟进日期",
    "未跟进天数",
    "提醒等级",
    "建议动作",
    "备注",
]

DEFAULT_FOLLOWUP_STATUS = "待开发"
DEFAULT_FOLLOWUP_COUNT = 0


def build_followup_tasks(
    customer_pool_file=CUSTOMER_POOL_FILE,
    output_file=OUTPUT_FILE,
):
    if not os.path.exists(customer_pool_file):
        print(f"[ERROR] Customer pool file not found: {customer_pool_file}")
        return empty_stats(output_file)

    try:
        df = pd.read_excel(customer_pool_file)
    except Exception as error:
        print(f"[ERROR] Failed to read customer pool: {error}")
        return empty_stats(output_file)

    df = ensure_followup_columns(df)
    today = date.today()
    tasks = []

    for _, row in df.iterrows():
        task = build_task(row, today)

        if task is not None:
            tasks.append(task)

    task_df = pd.DataFrame(tasks)

    for column in TASK_COLUMNS:
        if column not in task_df.columns:
            task_df[column] = ""

    task_df = task_df[TASK_COLUMNS]
    task_df = sort_tasks(task_df)

    df.to_excel(customer_pool_file, index=False, engine="openpyxl")
    task_df.to_excel(output_file, index=False, engine="openpyxl")

    stats = build_stats(df, task_df)

    print(f"[DONE] 客户总数：{stats['total_customers']}")
    print(f"[DONE] 待开发数量：{stats['pending_count']}")
    print(f"[DONE] 7天未跟进：{stats['days_7_count']}")
    print(f"[DONE] 14天未跟进：{stats['days_14_count']}")
    print(f"[DONE] 30天未跟进：{stats['days_30_count']}")
    print(f"[DONE] 导出文件：{output_file}")

    if task_df.empty:
        print("[WARNING] No follow-up tasks generated")

    return {
        **stats,
        "output_file": output_file,
    }


def ensure_followup_columns(df):
    for column in FOLLOWUP_COLUMNS:
        if column not in df.columns:
            df[column] = default_for_column(column)

    for column in ["企业名称", "行业", "电话", "邮箱", "开发状态", "备注"]:
        if column not in df.columns:
            df[column] = ""

    df["跟进状态"] = df["跟进状态"].apply(
        lambda value: clean_cell(value) or DEFAULT_FOLLOWUP_STATUS
    )
    df["跟进次数"] = df["跟进次数"].apply(
        lambda value: parse_int(value, DEFAULT_FOLLOWUP_COUNT)
    )

    return df


def build_task(row, today):
    followup_status = clean_cell(row.get("跟进状态", ""))
    development_status = clean_cell(row.get("开发状态", ""))
    last_followup_date = parse_date(row.get("最后跟进日期", ""))

    if followup_status == DEFAULT_FOLLOWUP_STATUS or development_status == "待开发":
        return task_from_row(
            row=row,
            days_without_followup=days_since(last_followup_date, today),
            reminder_level="高",
            action="立即联系",
        )

    if last_followup_date is None:
        return task_from_row(
            row=row,
            days_without_followup="",
            reminder_level="中",
            action="发送开发信",
        )

    days_without_followup = (today - last_followup_date).days

    if days_without_followup >= 30:
        return task_from_row(row, days_without_followup, "最高", "重新评估客户")

    if days_without_followup >= 14:
        return task_from_row(row, days_without_followup, "高", "电话联系")

    if days_without_followup >= 7:
        return task_from_row(row, days_without_followup, "中", "发送开发信")

    return None


def task_from_row(row, days_without_followup, reminder_level, action):
    return {
        "企业名称": clean_cell(row.get("企业名称", "")),
        "行业": clean_cell(row.get("行业", "")),
        "电话": clean_cell(row.get("电话", "")),
        "邮箱": clean_cell(row.get("邮箱", "")),
        "开发状态": clean_cell(row.get("开发状态", "")),
        "最后跟进日期": clean_cell(row.get("最后跟进日期", "")),
        "未跟进天数": days_without_followup,
        "提醒等级": reminder_level,
        "建议动作": action,
        "备注": clean_cell(row.get("备注", "")),
    }


def build_stats(customer_df, task_df):
    pending_count = int(
        (
            customer_df["开发状态"]
            .fillna("")
            .astype(str)
            .str.strip()
            == "待开发"
        ).sum()
    )

    numeric_days = pd.to_numeric(task_df["未跟进天数"], errors="coerce")

    return {
        "total_customers": len(customer_df),
        "pending_count": pending_count,
        "days_7_count": int(((numeric_days >= 7) & (numeric_days < 14)).sum()),
        "days_14_count": int(((numeric_days >= 14) & (numeric_days < 30)).sum()),
        "days_30_count": int((numeric_days >= 30).sum()),
    }


def sort_tasks(task_df):
    if task_df.empty:
        return task_df

    level_order = {
        "最高": 3,
        "高": 2,
        "中": 1,
    }
    task_df["_level_order"] = task_df["提醒等级"].map(level_order).fillna(0)
    task_df["_days_order"] = pd.to_numeric(
        task_df["未跟进天数"],
        errors="coerce",
    ).fillna(-1)
    task_df = task_df.sort_values(
        by=["_level_order", "_days_order"],
        ascending=[False, False],
    )
    return task_df.drop(columns=["_level_order", "_days_order"])


def default_for_column(column):
    if column == "跟进状态":
        return DEFAULT_FOLLOWUP_STATUS

    if column == "跟进次数":
        return DEFAULT_FOLLOWUP_COUNT

    return ""


def parse_date(value):
    text = clean_cell(value)

    if not text:
        return None

    try:
        return pd.to_datetime(text).date()
    except Exception:
        return None


def days_since(last_date, today):
    if last_date is None:
        return ""

    return (today - last_date).days


def parse_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clean_cell(value):
    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


def empty_stats(output_file):
    return {
        "total_customers": 0,
        "pending_count": 0,
        "days_7_count": 0,
        "days_14_count": 0,
        "days_30_count": 0,
        "output_file": output_file,
    }


if __name__ == "__main__":
    build_followup_tasks()
