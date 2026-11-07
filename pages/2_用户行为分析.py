# pages/2_用户行为分析.py
import pandas as pd
import streamlit as st

from config import CLEANED_DATA_FILE
from src.data_loader import load_csv
from src.visualization import (
    plot_country_sales,
    plot_monthly_sales,
    plot_purchase_conversion,
    plot_top_products,
    plot_user_monetary_distribution,
)


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.warning("请先登录")
        return
    st.caption(f"当前用户：{user['user_name']}（{user['role']}）")
    st.header("用户行为分析")

    if not CLEANED_DATA_FILE.exists():
        st.warning("未找到清洗后数据，请先到“数据接入与预处理”页面完成预处理。")
        return

    try:
        df = load_csv(CLEANED_DATA_FILE)
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    except Exception as exc:
        st.error(f"读取清洗数据失败: {exc}")
        return

    min_date = df["InvoiceDate"].min().date()
    max_date = df["InvoiceDate"].max().date()
    date_range = st.date_input("时间范围", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    countries = sorted(df["Country"].dropna().astype(str).unique().tolist()) if "Country" in df.columns else []
    selected_countries = st.multiselect("国家或地区", countries, default=countries[: min(5, len(countries))])

    filtered = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["InvoiceDate"].dt.date >= start) & (filtered["InvoiceDate"].dt.date <= end)
        ]
    if selected_countries and "Country" in filtered.columns:
        filtered = filtered[filtered["Country"].isin(selected_countries)]

    st.write("筛选后数据量：", filtered.shape)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_monthly_sales(filtered), width="stretch")
    with col2:
        st.plotly_chart(plot_top_products(filtered), width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(plot_user_monetary_distribution(filtered), width="stretch")
    with col4:
        st.plotly_chart(plot_country_sales(filtered), width="stretch")

    st.plotly_chart(plot_purchase_conversion(filtered), width="stretch")