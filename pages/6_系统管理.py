# pages/6_系统管理.py
import streamlit as st

from src.auth import list_users, set_user_enable, update_user
from src.logger import log_operation, query_logs
from src.utils import read_sqlite


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.warning("请先登录")
        return
    if user["role"] != "admin":
        st.error("仅管理员可访问系统管理页面。")
        return
    st.caption(f"当前用户：{user['user_name']}（{user['role']}）")
    st.header("系统管理")

    tab1, tab2, tab3 = st.tabs(["用户管理", "操作日志", "模型信息"])

    with tab1:
        users = list_users()
        st.dataframe(users, width="stretch")
        options = {f"{u['user_id']} - {u['user_name']}（{u['role']}）": int(u["user_id"]) for u in users}
        selected = st.selectbox("选择用户", list(options.keys()))
        user_id = options[selected]
        col1, col2 = st.columns(2)
        with col1:
            if st.button("启用该用户"):
                if set_user_enable(user_id, True):
                    log_operation(int(user["user_id"]), "用户管理", f"启用用户ID={user_id}")
                    st.success("已启用")
                    st.rerun()
        with col2:
            if st.button("禁用该用户"):
                if set_user_enable(user_id, False):
                    log_operation(int(user["user_id"]), "用户管理", f"禁用用户ID={user_id}")
                    st.success("已禁用")
                    st.rerun()

        new_password = st.text_input("重置密码", type="password")
        if st.button("重置该用户密码"):
            if not new_password:
                st.error("请输入新密码")
            elif update_user(user_id, password=new_password):
                log_operation(int(user["user_id"]), "用户管理", f"重置用户ID={user_id}密码")
                st.success("密码已重置")
            else:
                st.error("密码重置失败")

    with tab2:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            user_id_filter = st.number_input("用户ID（0表示全部）", min_value=0, value=0, step=1)
        with col2:
            operate_type = st.text_input("操作类型")
        with col3:
            start_time = st.text_input("开始时间", placeholder="YYYY-MM-DD HH:MM:SS")
        with col4:
            end_time = st.text_input("结束时间", placeholder="YYYY-MM-DD HH:MM:SS")
        logs = query_logs(
            user_id=int(user_id_filter) if user_id_filter > 0 else None,
            operate_type=operate_type or None,
            start_time=start_time or None,
            end_time=end_time or None,
        )
        st.dataframe(logs, width="stretch")

    with tab3:
        models = read_sqlite("SELECT * FROM sys_model_info ORDER BY model_id DESC")
        st.dataframe(models, width="stretch")