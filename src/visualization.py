# src/visualization.py
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title)
    return fig


def plot_monthly_sales(df: pd.DataFrame) -> go.Figure:
    """月度销售额折线图。"""
    if df.empty or "InvoiceDate" not in df.columns:
        return _empty_fig("月度销售额趋势")
    data = df.copy()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Amount"] = pd.to_numeric(data["Quantity"], errors="coerce") * pd.to_numeric(data["UnitPrice"], errors="coerce")
    data["Month"] = data["InvoiceDate"].dt.to_period("M").astype(str)
    monthly = data.groupby("Month", as_index=False)["Amount"].sum().sort_values("Month")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Amount"], mode="lines+markers", name="销售额"))
    fig.update_layout(title="月度销售额趋势", xaxis_title="月份", yaxis_title="销售额")
    return fig


def plot_top_products(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """商品销量排行柱状图。"""
    if df.empty or "Quantity" not in df.columns:
        return _empty_fig("商品销量排行")
    data = df.copy()
    product_col = "Description" if "Description" in data.columns else "StockCode"
    data[product_col] = data[product_col].fillna("未知商品").astype(str)
    top = data.groupby(product_col, as_index=False)["Quantity"].sum().nlargest(top_n, "Quantity")
    fig = go.Figure(go.Bar(x=top["Quantity"], y=top[product_col], orientation="h"))
    fig.update_layout(title=f"商品销量排行 TOP{top_n}", xaxis_title="销量", yaxis_title="商品")
    return fig


def plot_user_monetary_distribution(df: pd.DataFrame) -> go.Figure:
    """用户消费金额分布直方图。"""
    if df.empty or "CustomerID" not in df.columns:
        return _empty_fig("用户消费金额分布")
    data = df.copy()
    data["Amount"] = pd.to_numeric(data["Quantity"], errors="coerce") * pd.to_numeric(data["UnitPrice"], errors="coerce")
    monetary = data.groupby("CustomerID", as_index=False)["Amount"].sum()
    fig = go.Figure(go.Histogram(x=monetary["Amount"], nbinsx=50))
    fig.update_layout(title="用户消费金额分布", xaxis_title="消费金额", yaxis_title="用户数")
    return fig


def plot_country_sales(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """国家或地区销售额柱状图。"""
    if df.empty or "Country" not in df.columns:
        return _empty_fig("国家或地区销售额")
    data = df.copy()
    data["Amount"] = pd.to_numeric(data["Quantity"], errors="coerce") * pd.to_numeric(data["UnitPrice"], errors="coerce")
    country = data.groupby("Country", as_index=False)["Amount"].sum().nlargest(top_n, "Amount")
    fig = go.Figure(go.Bar(x=country["Country"], y=country["Amount"]))
    fig.update_layout(title=f"国家或地区销售额 TOP{top_n}", xaxis_title="国家或地区", yaxis_title="销售额")
    return fig


def plot_purchase_conversion(df: pd.DataFrame) -> go.Figure:
    """购买转化率饼图。"""
    if df.empty or "CustomerID" not in df.columns:
        return _empty_fig("购买转化率")
    data = df.copy()
    data["Amount"] = pd.to_numeric(data["Quantity"], errors="coerce") * pd.to_numeric(data["UnitPrice"], errors="coerce")
    users = set(data["CustomerID"].dropna().unique())
    buyers = set(data.loc[data["Amount"] > 0, "CustomerID"].dropna().unique())
    not_buyers = users - buyers
    fig = go.Figure(
        go.Pie(
            labels=["有购买记录", "无购买记录"],
            values=[len(buyers), len(not_buyers)],
            hole=0.4,
        )
    )
    fig.update_layout(title="购买转化率")
    return fig


def plot_rfm_segments(rfm_df: pd.DataFrame) -> go.Figure:
    """RFM用户分层占比饼图。"""
    if rfm_df.empty or "Segment" not in rfm_df.columns:
        return _empty_fig("RFM用户分层")
    counts = rfm_df["Segment"].value_counts().reset_index()
    counts.columns = ["Segment", "Count"]
    fig = go.Figure(go.Pie(labels=counts["Segment"], values=counts["Count"], hole=0.4))
    fig.update_layout(title="RFM用户分层占比")
    return fig

# src/visualization.py 中的对应函数
def plot_cluster_scatter(features: pd.DataFrame, labels: np.ndarray) -> go.Figure:
    """聚类散点图，使用Monetary和Frequency两维。使用 Scattergl 提升渲染性能"""
    if features.empty or "Monetary" not in features.columns or "Frequency" not in features.columns:
        return _empty_fig("用户聚类散点图")
        
    # 数据清理：防止空值或无穷大导致前端渲染卡死
    data = features[["Monetary", "Frequency"]].copy()
    data["Monetary"] = pd.to_numeric(data["Monetary"], errors="coerce").fillna(0)
    data["Frequency"] = pd.to_numeric(data["Frequency"], errors="coerce").fillna(0)
    
    # 如果存在极端值（比如极少数用户消费额特别高），使用对数缩放以免图表被拉扁
    # 你也可以选择注释掉下面两行以使用原始值
    # data["Monetary"] = np.log1p(data["Monetary"])
    # data["Frequency"] = np.log1p(data["Frequency"])

    data["Cluster"] = labels.astype(str)
    
    fig = go.Figure()
    for cluster in sorted(data["Cluster"].unique()):
        part = data[data["Cluster"] == cluster]
        fig.add_trace(
            # 使用 Scattergl (WebGL 加速) 解决 4000+ 数据点的卡顿问题
            go.Scattergl(
                x=part["Frequency"],
                y=part["Monetary"],
                mode="markers",
                name=f"簇 {cluster}",
                marker={"size": 6, "opacity": 0.8}, 
            )
        )
    fig.update_layout(
        title="用户聚类散点图", 
        xaxis_title="Frequency (购买频次)", 
        yaxis_title="Monetary (总金额)"
    )
    return fig

def plot_model_comparison(results: dict) -> go.Figure:
    """多模型指标对比柱状图。"""
    if not results:
        return _empty_fig("多模型指标对比")
    metrics = ["Accuracy", "Precision", "Recall", "F1", "AUC"]
    algorithms = list(results.keys())
    fig = go.Figure()
    for metric in metrics:
        values = [results[alg].get(metric, 0.0) for alg in algorithms]
        fig.add_trace(go.Bar(x=algorithms, y=values, name=metric))
    fig.update_layout(title="多模型指标对比", xaxis_title="算法", yaxis_title="指标值", barmode="group")
    return fig