"""Infrastructure-only helpers for safe Excel reads and writes.

This module deliberately contains no filtering, scoring, deduplication, or other
BidRadar business rules.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


class ExcelSafetyError(RuntimeError):
    """Base exception for safe Excel operations."""


class ExcelReadError(ExcelSafetyError):
    """Raised when an existing Excel workbook cannot be read safely."""


class ExcelWriteError(ExcelSafetyError):
    """Raised when an Excel workbook cannot be written safely."""


class ExcelValidationError(ExcelSafetyError):
    """Raised when a DataFrame does not satisfy a column contract."""


def read_excel_safe(path, required_columns=None, **read_kwargs):
    """Read an Excel workbook or raise a descriptive exception.

    Missing, damaged, locked, or otherwise unreadable workbooks are never
    converted to an empty DataFrame.
    """
    excel_path = _as_path(path)

    if not excel_path.is_file():
        raise ExcelReadError(f"Excel file does not exist: {excel_path}")

    try:
        dataframe = pd.read_excel(excel_path, **read_kwargs)
    except Exception as error:
        raise ExcelReadError(f"Failed to read Excel file: {excel_path}") from error

    if required_columns is not None:
        validate_columns(dataframe, required_columns)

    return dataframe


def write_excel_safe(
    dataframe,
    path,
    required_columns=None,
    *,
    backup=True,
    backup_dir=None,
    index=False,
    engine="openpyxl",
    **write_kwargs,
):
    """Write a DataFrame through a verified temporary workbook.

    An existing destination is backed up only after the temporary workbook has
    been written and read back successfully. The final replacement uses
    ``os.replace`` so the destination is never partially written.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    excel_path = _as_path(path)
    if required_columns is not None:
        validate_columns(dataframe, required_columns)

    parent = excel_path.parent
    if not parent.is_dir():
        raise ExcelWriteError(f"Destination directory does not exist: {parent}")

    original_exists = excel_path.is_file()
    backup_path = None
    temporary_path = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{excel_path.stem}.",
            suffix=excel_path.suffix or ".xlsx",
            dir=parent,
        )
        os.close(file_descriptor)
        temporary_path = Path(temporary_name)

        dataframe.to_excel(
            temporary_path,
            index=index,
            engine=engine,
            **write_kwargs,
        )
        verified = read_excel_safe(temporary_path)
        _validate_round_trip(dataframe, verified, index=index)

        if original_exists and backup:
            backup_path = backup_excel(excel_path, backup_dir=backup_dir)

        os.replace(temporary_path, excel_path)
        temporary_path = None

        saved = read_excel_safe(excel_path)
        _validate_round_trip(dataframe, saved, index=index)
    except Exception as error:
        if original_exists and backup_path is not None:
            try:
                shutil.copy2(backup_path, excel_path)
            except Exception as rollback_error:
                raise ExcelWriteError(
                    f"Failed to write {excel_path}; rollback also failed"
                ) from rollback_error
        elif not original_exists and excel_path.exists():
            try:
                excel_path.unlink()
            except OSError:
                pass

        if isinstance(error, ExcelWriteError):
            raise
        raise ExcelWriteError(f"Failed to write Excel file: {excel_path}") from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass

    return {
        "path": excel_path,
        "backup_path": backup_path,
        "summary": build_excel_summary(saved, path=excel_path),
    }


def backup_excel(path, backup_dir=None):
    """Copy an existing workbook to a timestamped backup and return its path."""
    excel_path = _as_path(path)
    if not excel_path.is_file():
        raise ExcelReadError(f"Excel file does not exist: {excel_path}")

    target_dir = _as_path(backup_dir) if backup_dir is not None else excel_path.parent / "backup" / "auto" / excel_path.stem
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = target_dir / f"{timestamp}_{excel_path.name}"
        shutil.copy2(excel_path, backup_path)
    except Exception as error:
        raise ExcelWriteError(f"Failed to back up Excel file: {excel_path}") from error

    return backup_path


def validate_columns(dataframe, required_columns):
    """Raise when any required column is missing; never reorder the DataFrame."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    required = _normalize_columns(required_columns)
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ExcelValidationError(
            "Missing required Excel columns: " + ", ".join(map(str, missing))
        )

    return dataframe


def ensure_columns(dataframe, columns, fill_value="", *, keep_extra=True):
    """Return a copy with requested columns present and in the requested order."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    requested = _normalize_columns(columns)
    result = dataframe.copy()
    for column in requested:
        if column not in result.columns:
            result[column] = fill_value

    extras = [column for column in result.columns if column not in requested]
    ordered_columns = requested + extras if keep_extra else requested
    return result.loc[:, ordered_columns]


def build_excel_summary(dataframe, path=None):
    """Return a small structural summary without changing data."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    return {
        "path": _as_path(path) if path is not None else None,
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "columns": list(dataframe.columns),
    }


def _as_path(path):
    if not isinstance(path, (str, os.PathLike)):
        raise TypeError("path must be a string or path-like object")
    return Path(path).expanduser()


def _normalize_columns(columns: Iterable):
    if isinstance(columns, (str, bytes)):
        raise TypeError("columns must be an iterable of column names")
    return list(columns)


def _validate_round_trip(expected, actual, *, index):
    expected_columns = list(expected.columns)
    if index:
        actual_columns = list(actual.columns[1:])
    else:
        actual_columns = list(actual.columns)

    if actual_columns != expected_columns:
        raise ExcelWriteError(
            "Excel column order changed during write: "
            f"expected {expected_columns}, got {actual_columns}"
        )
    if len(actual) != len(expected):
        raise ExcelWriteError(
            "Excel row count changed during write: "
            f"expected {len(expected)}, got {len(actual)}"
        )
