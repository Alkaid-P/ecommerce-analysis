# pages/1_数据接入与预处理.py
import streamlit as st

from config import CLEANED_DATA_FILE, RAW_DATA_FILE, USER_FEATURE_FILE
from src.data_loader import get_data_preview, load_csv, load_uploaded_file, save_dataframe
from src.feature_engineering import build_user_features
from src.logger import log_operation
from src.preprocessing import clean_data, get_preprocess_report


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.warning("请先登录")
        return
    st.caption(f"当前用户：{user['user_name']}（{user['role']}）")
    st.header("数据接入与预处理")

    uploaded = st.file_uploader("上传 Online Retail CSV 文件", type=["csv"])
    df = None
    if uploaded is not None:
        try:
            df = load_uploaded_file(uploaded)
            save_dataframe(df, RAW_DATA_FILE)
            st.success("上传文件已读取并保存到 data/raw/online_retail.csv")
            log_operation(int(user["user_id"]), "数据接入", "上传原始数据文件")
        except Exception as exc:
            st.error(f"读取上传文件失败: {exc}")
    elif RAW_DATA_FILE.exists():
        try:
            df = load_csv(RAW_DATA_FILE)
            st.info("已从 data/raw/online_retail.csv 加载数据")
        except Exception as exc:
            st.error(f"加载原始数据失败: {exc}")

    if df is None:
        st.info("请上传CSV文件，或将 online_retail.csv 放到 data/raw/ 目录。")
        return

    st.subheader("数据预览")
    st.dataframe(get_data_preview(df, 10), width="stretch")
    st.write("数据规模：", df.shape)

    if st.button("开始预处理"):
        try:
            with st.spinner("正在清洗数据并生成用户特征..."):
                cleaned, report = clean_data(df)
                save_dataframe(cleaned, CLEANED_DATA_FILE)
                features = build_user_features(cleaned)
                save_dataframe(features, USER_FEATURE_FILE)
                log_operation(
                    int(user["user_id"]),
                    "数据预处理",
                    f"清洗后{len(cleaned)}行，生成用户特征{len(features)}行",
                )
            st.success("预处理完成，已保存清洗数据和用户特征表。")
            st.subheader("清洗统计")
            st.json(report)
            st.subheader("清洗后质量报告")
            st.json(get_preprocess_report(cleaned))
            st.subheader("用户特征预览")
            st.dataframe(features.head(20), width="stretch")
        except Exception as exc:
            st.error(f"预处理失败: {exc}")
            log_operation(int(user["user_id"]), "数据预处理", "预处理失败", "失败", str(exc))