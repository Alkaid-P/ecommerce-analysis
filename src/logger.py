# src/logger.py
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config import LOG_FILE
from src.utils import execute_sqlite, read_sqlite

# 配置专属的文件日志记录器
file_logger = logging.getLogger("SystemFileLogger")
file_logger.setLevel(logging.INFO)

# 防止 Streamlit 热重载时重复添加 Handler
if not file_logger.handlers:
    # 单个日志文件最大 5MB，最多保留 3 个备份 (system.log.1, system.log.2...)
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    file_logger.addHandler(handler)


def log_operation(
    user_id: int,
    operate_type: str,
    operate_content: str,
    result: str = "成功",
    error_msg: str = "",
) -> None:
    """写入操作日志到数据库和本地日志文件。"""
    # 1. 写入 SQLite 数据库 (供页面展示)
    execute_sqlite(
        """
        INSERT INTO sys_operation_log
        (user_id, operate_type, operate_content, operate_time, operate_result, error_msg)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            operate_type,
            operate_content,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            result,
            error_msg,
        ),
    )
    
    # 2. 写入本地日志文件 (供管理员排查)
    log_msg = f"用户[{user_id}] | {operate_type} | {result} | {operate_content}"
    if error_msg:
        log_msg += f" | 错误详情: {error_msg}"
        
    if result == "成功":
        file_logger.info(log_msg)
    else:
        file_logger.warning(log_msg)


def query_logs(
    user_id: int = None,
    operate_type: str = None,
    start_time: str = None,
    end_time: str = None,
) -> list[dict]:
    """查询日志（从数据库读取供页面展示）。"""
    sql = "SELECT * FROM sys_operation_log WHERE 1=1"
    params: list = []
    if user_id is not None:
        sql += " AND user_id = ?"
        params.append(user_id)
    if operate_type:
        sql += " AND operate_type LIKE ?"
        params.append(f"%{operate_type}%")
    if start_time:
        sql += " AND operate_time >= ?"
        params.append(start_time)
    if end_time:
        sql += " AND operate_time <= ?"
        params.append(end_time)
    sql += " ORDER BY log_id DESC LIMIT 1000"
    return read_sqlite(sql, tuple(params))