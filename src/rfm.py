# src/rfm.py
import pandas as pd


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """计算RFM基础指标。"""
    if df.empty:
        return pd.DataFrame(columns=["CustomerID", "Recency", "Frequency", "Monetary"])
    data = df.copy()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Amount"] = pd.to_numeric(data["Quantity"], errors="coerce") * pd.to_numeric(data["UnitPrice"], errors="coerce")
    max_date = data["InvoiceDate"].max()
    rfm = data.groupby("CustomerID").agg(
        LastPurchaseDate=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Amount", "sum"),
    ).reset_index()
    rfm["Recency"] = (max_date - rfm["LastPurchaseDate"]).dt.days
    rfm["Recency"] = rfm["Recency"].fillna(0).astype(int)
    return rfm[["CustomerID", "Recency", "Frequency", "Monetary"]]


def _score_series(series: pd.Series, bins: int, higher_is_better: bool) -> pd.Series:
    n_unique = series.nunique()
    n_bins = min(bins, n_unique)
    if n_bins < 2:
        return pd.Series([3] * len(series), index=series.index)
    ranks = pd.qcut(series.rank(method="first"), q=n_bins, labels=False, duplicates="drop") + 1
    if higher_is_better:
        return ranks.astype(int)
    return (n_bins + 1 - ranks).astype(int)


def score_rfm(rfm_df: pd.DataFrame, bins: int = 5) -> pd.DataFrame:
    """对R、F、M分箱打分。"""
    result = rfm_df.copy()
    result["R_score"] = _score_series(result["Recency"], bins, higher_is_better=False)
    result["F_score"] = _score_series(result["Frequency"], bins, higher_is_better=True)
    result["M_score"] = _score_series(result["Monetary"], bins, higher_is_better=True)
    result["RFM_score"] = result["R_score"] + result["F_score"] + result["M_score"]
    return result


def segment_users(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """根据RFM_score划分用户层级。"""
    result = rfm_df.copy()

    def _segment(score: int) -> str:
        if score >= 12:
            return "高价值客户"
        if score >= 9:
            return "潜力客户"
        if score >= 6:
            return "一般客户"
        if score >= 4:
            return "沉睡客户"
        return "流失风险客户"

    result["Segment"] = result["RFM_score"].apply(_segment)
    return result


def get_segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """统计各层级人数及平均RFM。"""
    return (
        rfm_df.groupby("Segment", as_index=False)
        .agg(
            人数=("CustomerID", "count"),
            平均Recency=("Recency", "mean"),
            平均Frequency=("Frequency", "mean"),
            平均Monetary=("Monetary", "mean"),
        )
        .sort_values("人数", ascending=False)
    )