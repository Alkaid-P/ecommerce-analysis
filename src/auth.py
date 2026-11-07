# src/auth.py
import sqlite3
from typing import Any

import bcrypt

from src.utils import execute_sqlite, read_sqlite


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def init_db() -> None:
    """初始化SQLite数据库并创建默认管理员。"""
    execute_sqlite(
        """
        CREATE TABLE IF NOT EXISTS sys_user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            real_name VARCHAR(30),
            role VARCHAR(20) NOT NULL CHECK(role IN ('admin','analyst','operator')),
            phone VARCHAR(20),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_enable INTEGER DEFAULT 1
        )
        """
    )
    execute_sqlite(
        """
        CREATE TABLE IF NOT EXISTS sys_operation_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            operate_type VARCHAR(50),
            operate_content TEXT,
            operate_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            operate_result VARCHAR(20),
            error_msg TEXT
        )
        """
    )
    execute_sqlite(
        """
        CREATE TABLE IF NOT EXISTS sys_model_info (
            model_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name VARCHAR(50),
            model_task VARCHAR(30),
            algorithm VARCHAR(30),
            model_file_path VARCHAR(200),
            train_param TEXT,
            eval_index TEXT,
            create_user_id INTEGER,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    admin = read_sqlite("SELECT user_id FROM sys_user WHERE user_name = ?", ("admin",))
    if not admin:
        execute_sqlite(
            """
            INSERT INTO sys_user (user_name, password, real_name, role, phone, is_enable)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            ("admin", _hash_password("admin123"), "系统管理员", "admin", ""),
        )


def create_user(user_name: str, password: str, real_name: str, role: str, phone: str) -> tuple[bool, str]:
    """注册用户。"""
    if role not in ("admin", "analyst", "operator"):
        return False, "角色不合法"
    if not user_name or not password:
        return False, "用户名和密码不能为空"
    exists = read_sqlite("SELECT user_id FROM sys_user WHERE user_name = ?", (user_name,))
    if exists:
        return False, "用户名已存在"
    ok = execute_sqlite(
        """
        INSERT INTO sys_user (user_name, password, real_name, role, phone, is_enable)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (user_name, _hash_password(password), real_name, role, phone),
    )
    return (True, "注册成功") if ok else (False, "注册失败")


def verify_login(user_name: str, password: str) -> dict | None:
    """登录验证。"""
    rows = read_sqlite("SELECT * FROM sys_user WHERE user_name = ?", (user_name,))
    if not rows:
        return None
    user = rows[0]
    if int(user.get("is_enable", 1)) != 1:
        return None
    if not _check_password(password, str(user["password"])):
        return None
    user.pop("password", None)
    return user


def get_user_by_id(user_id: int) -> dict | None:
    rows = read_sqlite("SELECT user_id,user_name,real_name,role,phone,create_time,is_enable FROM sys_user WHERE user_id = ?", (user_id,))
    return rows[0] if rows else None


def update_user(user_id: int, **kwargs) -> bool:
    """更新用户信息。"""
    allowed = {"user_name", "password", "real_name", "role", "phone", "is_enable"}
    fields = []
    values: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        if key == "password":
            value = _hash_password(str(value))
        if key == "role" and value not in ("admin", "analyst", "operator"):
            continue
        fields.append(f"{key} = ?")
        values.append(value)
    if not fields:
        return False
    values.append(user_id)
    return execute_sqlite(f"UPDATE sys_user SET {', '.join(fields)} WHERE user_id = ?", tuple(values))


def list_users() -> list[dict]:
    return read_sqlite(
        "SELECT user_id,user_name,real_name,role,phone,create_time,is_enable FROM sys_user ORDER BY user_id"
    )


def set_user_enable(user_id: int, enable: bool) -> bool:
    return execute_sqlite("UPDATE sys_user SET is_enable = ? WHERE user_id = ?", (1 if enable else 0, user_id))