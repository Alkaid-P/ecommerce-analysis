# pages/4_用户聚类.py
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from config import DEFAULT_CLUSTER_K, MODEL_DIR, USER_FEATURE_FILE
from src.clustering import (
    elbow_method,
    get_cluster_summary,
    prepare_cluster_features,
    save_kmeans_model,
    train_kmeans,
)
from src.data_loader import load_csv, save_dataframe
from src.logger import log_operation
from src.visualization import plot_cluster_scatter


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.warning("请先登录")
        return
    st.caption(f"当前用户：{user['user_name']}（{user['role']}）")
    st.header("用户聚类")

    if not USER_FEATURE_FILE.exists():
        st.warning("未找到用户特征表，请先完成数据预处理。")
        return

    try:
        features = load_csv(USER_FEATURE_FILE)
        X_scaled_df = prepare_cluster_features(features)
    except Exception as exc:
        st.error(f"准备聚类特征失败: {exc}")
        return

    st.dataframe(features.head(20), width="stretch")
    k = st.slider("聚类簇数 K", min_value=2, max_value=10, value=DEFAULT_CLUSTER_K)

    if st.button("计算肘部法则"):
        sse = elbow_method(X_scaled_df.values, max_k=10)
        fig = go.Figure(go.Scatter(x=list(range(2, 11)), y=sse, mode="lines+markers"))
        fig.update_layout(title="肘部法则", xaxis_title="K", yaxis_title="SSE")
        st.plotly_chart(fig, width="stretch")

    # 使用 session_state 缓存训练结果
    if "kmeans_result" not in st.session_state:
        st.session_state["kmeans_result"] = None

    if st.button("训练K-Means并保存"):
        try:
            # 耗时计算：不需要 st.rerun()
            model, labels = train_kmeans(X_scaled_df.values, k)
            summary = get_cluster_summary(features, labels)
            labeled = features.copy()
            labeled["Cluster"] = labels
            
            model_path = MODEL_DIR / "kmeans_user.pkl"
            save_kmeans_model(model, model_path)
            save_dataframe(labeled, USER_FEATURE_FILE.parent / "user_clusters.csv")
            log_operation(int(user["user_id"]), "用户聚类", f"训练K-Means，K={k}，用户数{len(features)}")
            
            # 将结果保存到 session_state
            st.session_state["kmeans_result"] = {
                "labels": labels,
                "summary": summary,
                "labeled": labeled
            }
        except Exception as exc:
            st.error(f"聚类训练失败: {exc}")
            log_operation(int(user["user_id"]), "用户聚类", "聚类训练失败", "失败", str(exc))

    # 渲染结果区
    if st.session_state["kmeans_result"] is not None:
        res = st.session_state["kmeans_result"]
        st.success("K-Means训练完成，模型和带聚类标签数据已保存。")
        
        # 渲染图表
        st.plotly_chart(plot_cluster_scatter(features, np.array(res["labels"])), width="stretch")
        
        st.subheader("各簇统计")
        st.dataframe(res["summary"], width="stretch")
        
        # 下载按钮
        csv_data = res["labeled"].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="下载带聚类标签用户数据",
            data=csv_data,
            file_name="user_clusters.csv",
            mime="text/csv",
        )