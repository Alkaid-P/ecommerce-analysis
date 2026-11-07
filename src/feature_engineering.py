# src/feature_engineering.py
import pandas as pd


def build_user_features(df: pd.DataFrame) -> pd.DataFrame:
    """按CustomerID聚合生成用户特征表。"""
    if df.empty or "CustomerID" not in df.columns:
        return pd.DataFrame(
            columns=[
                "CustomerID", "Recency", "Frequency", "Monetary",
                "TotalQuantity", "AvgOrderValue", "UniqueProducts", "ActiveDays",
            ]
        )

    data = df.copy()
    if "InvoiceDate" in data.columns:
        data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Amount"] = pd.to_numeric(data["Quantity"], errors="coerce") * pd.to_numeric(data["UnitPrice"], errors="coerce")
    max_date = data["InvoiceDate"].max()

    grouped = data.groupby("CustomerID").agg(
        LastPurchaseDate=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Amount", "sum"),
        TotalQuantity=("Quantity", "sum"),
        UniqueProducts=("StockCode", "nunique"),
        ActiveDays=("InvoiceDate", lambda s: s.dt.date.nunique()),
    ).reset_index()

    grouped["Recency"] = (max_date - grouped["LastPurchaseDate"]).dt.days
    grouped["AvgOrderValue"] = grouped["Monetary"] / grouped["Frequency"].replace(0, pd.NA)
    grouped["AvgOrderValue"] = grouped["AvgOrderValue"].fillna(0.0)
    grouped["Recency"] = grouped["Recency"].fillna(0).astype(int)

    result = grouped[
        ["CustomerID", "Recency", "Frequency", "Monetary", "TotalQuantity",
         "AvgOrderValue", "UniqueProducts", "ActiveDays"]
    ].copy()
    return result


def build_purchase_label(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """构造购买预测标签。"""
    if df.empty or "CustomerID" not in df.columns:
        return pd.DataFrame(columns=["CustomerID", "buy_label"])
    data = df.copy()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    max_date = data["InvoiceDate"].max()
    last_purchase = data.groupby("CustomerID")["InvoiceDate"].max().reset_index()
    last_purchase["buy_label"] = (
        (max_date - last_purchase["InvoiceDate"]).dt.days <= days
    ).astype(int)
    return last_purchase[["CustomerID", "buy_label"]]


def build_churn_label(user_features: pd.DataFrame, threshold_days: int = 90) -> pd.DataFrame:
    """构造流失标签。"""
    result = user_features[["CustomerID"]].copy()
    result["churn_label"] = (user_features["Recency"] > threshold_days).astype(int)
    return result


def merge_features_and_labels(features: pd.DataFrame, labels: pd.DataFrame, label_col: str) -> pd.DataFrame:
    """合并特征和标签。"""
    if label_col not in labels.columns:
        raise ValueError(f"标签列不存在: {label_col}")
    return features.merge(labels[["CustomerID", label_col]], on="CustomerID", how="inner")