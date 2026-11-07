# src/data_loader.py
from pathlib import Path
from typing import Any

import pandas as pd


def load_csv(file_path: Path) -> pd.DataFrame:
    """读取CSV文件。"""
    try:
        return pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return pd.read_csv(file_path, encoding="latin1")
        except Exception as exc:
            raise ValueError(f"读取CSV失败: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"读取CSV失败: {exc}") from exc


def load_uploaded_file(uploaded_file: Any) -> pd.DataFrame:
    """读取Streamlit上传的CSV文件。"""
    try:
        return pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1")
    except Exception as exc:
        raise ValueError(f"读取上传文件失败: {exc}") from exc


def save_dataframe(df: pd.DataFrame, file_path: Path) -> None:
    """保存DataFrame到CSV。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")


def get_data_preview(df: pd.DataFrame, rows: int = 5) -> pd.DataFrame:
    """返回数据前几行。"""
    return df.head(rows)