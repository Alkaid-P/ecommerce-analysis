# pages/3_RFM价值分析.py
import streamlit as st

from config import CLEANED_DATA_FILE
from src.data_loader import load_csv
from src.logger import log_operation
from src.rfm import compute_rfm, get_segment_summary, score_rfm, segment_users
from src.visualization import plot_rfm_segments


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.warning("请先登录")
        return
    st.caption(f"当前用户：{user['user_name']}（{user['role']}）")
    st.header("RFM价值分析")

    if not CLEANED_DATA_FILE.exists():
        st.warning("未找到清洗后数据，请先完成数据预处理。")
        return

    try:
        df = load_csv(CLEANED_DATA_FILE)
        rfm = compute_rfm(df)
        scored = score_rfm(rfm)
        segmented = segment_users(scored)
        summary = get_segment_summary(segmented)
        log_operation(int(user["user_id"]), "RFM分析", f"完成{len(segmented)}名用户RFM分层")
    except Exception as exc:
        st.error(f"RFM分析失败: {exc}")
        return

    st.plotly_chart(plot_rfm_segments(segmented), width="stretch")
    st.subheader("各层级统计")
    st.dataframe(summary, width="stretch")

    st.subheader("用户分层名单")
    st.dataframe(segmented, width="stretch")

    csv_data = segmented.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "下载RFM分层名单CSV",
        data=csv_data,
        file_name="rfm_segments.csv",
        mime="text/csv",
    )