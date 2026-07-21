"""
BidRadar V1.4 daily report.

Read final bid_results.xlsx and generate daily_report.txt.
"""

from datetime import datetime
import os
from pathlib import Path
import shutil
import tempfile

import pandas as pd

from utils.excel_helper import read_excel_safe


REPORT_FILE = "daily_report.txt"


def generate_daily_report(excel_file, report_file=REPORT_FILE):
    """根据最终导出的 Excel 生成文本日报。"""
    try:
        df = read_excel_safe(excel_file)
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

    write_text_safe("\n".join(lines), report_file)

    print(f"日报文件：{report_file}")
    return report_file


class TextWriteError(RuntimeError):
    """Raised when a text output cannot be replaced safely."""


def write_text_safe(content, path, *, encoding="utf-8", backup=True):
    """Write text through a verified temporary file with optional backup."""
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    output_path = Path(path)
    parent = output_path.parent
    if not parent.is_dir():
        raise TextWriteError(f"Destination directory does not exist: {parent}")

    original_exists = output_path.is_file()
    backup_path = None
    temporary_path = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.stem}.",
            suffix=output_path.suffix or ".txt",
            dir=parent,
        )
        os.close(file_descriptor)
        temporary_path = Path(temporary_name)
        temporary_path.write_text(content, encoding=encoding)

        if temporary_path.read_text(encoding=encoding) != content:
            raise TextWriteError(
                f"Text encoding verification failed: {output_path}"
            )

        if original_exists and backup:
            backup_path = _backup_text(output_path)

        os.replace(temporary_path, output_path)
        temporary_path = None

        if output_path.read_text(encoding=encoding) != content:
            raise TextWriteError(
                f"Text verification failed after replacement: {output_path}"
            )
    except Exception as error:
        if original_exists and backup_path is not None:
            try:
                shutil.copy2(backup_path, output_path)
            except Exception as rollback_error:
                raise TextWriteError(
                    f"Failed to write {output_path}; rollback also failed"
                ) from rollback_error
        elif not original_exists and output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass

        if isinstance(error, TextWriteError):
            raise
        raise TextWriteError(f"Failed to write text file: {output_path}") from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass

    return {
        "path": output_path,
        "backup_path": backup_path,
        "encoding": encoding,
        "character_count": len(content),
    }


def _backup_text(path):
    backup_dir = path.parent / "backup" / "auto" / path.stem
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = backup_dir / f"{timestamp}_{path.name}"
    shutil.copy2(path, backup_path)
    return backup_path
