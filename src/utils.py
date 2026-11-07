# src/utils.py
import sqlite3
import logging
from typing import Any

from config import DB_PATH, ensure_dirs as config_ensure_dirs

sys_logger = logging.getLogger("SystemFileLogger")

def format_currency(value: float) -> str:
    """格式化金额。"""
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "¥0.00"


def ensure_dirs() -> None:
    """创建所有必要目录。"""
    config_ensure_dirs()


def read_sqlite(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    """执行查询并返回字典列表。"""
    ensure_dirs()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_sqlite(query: str, params: tuple = ()) -> bool:
    """执行增删改语句。"""
    ensure_dirs()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(query, params)
            conn.commit()
        return True
    except Exception as exc:
        # 直接写入错误日志文件
        sys_logger.error(f"SQLite执行失败: {exc} | Query: {query}")
        return False