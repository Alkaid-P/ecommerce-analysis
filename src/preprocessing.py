# src/preprocessing.py
import pandas as pd


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """清洗电商交易数据并返回统计报告。"""
    report: dict = {}
    data = df.copy()
    report["原始行数"] = len(data)

    if "CustomerID" in data.columns:
        before = len(data)
        data = data[data["CustomerID"].notna()]
        report["删除CustomerID为空行数"] = before - len(data)

    if "Quantity" in data.columns:
        before = len(data)
        data = data[pd.to_numeric(data["Quantity"], errors="coerce") > 0]
        report["删除Quantity<=0行数"] = before - len(data)

    if "UnitPrice" in data.columns:
        before = len(data)
        data = data[pd.to_numeric(data["UnitPrice"], errors="coerce") > 0]
        report["删除UnitPrice<=0行数"] = before - len(data)

    if "InvoiceNo" in data.columns:
        before = len(data)
        data = data[~data["InvoiceNo"].astype(str).str.upper().str.startswith("C")]
        report["删除退货记录行数"] = before - len(data)

    before = len(data)
    data = data.drop_duplicates()
    report["删除重复行数"] = before - len(data)

    if "InvoiceDate" in data.columns:
        before = len(data)
        data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
        data = data[data["InvoiceDate"].notna()]
        report["删除日期无效行数"] = before - len(data)
        data["Year"] = data["InvoiceDate"].dt.year
        data["Month"] = data["InvoiceDate"].dt.month
        data["Day"] = data["InvoiceDate"].dt.day
        data["Hour"] = data["InvoiceDate"].dt.hour
        data["Weekday"] = data["InvoiceDate"].dt.weekday

    if "CustomerID" in data.columns:
        data["CustomerID"] = data["CustomerID"].astype(int)

    report["清洗后行数"] = len(data)
    return data.reset_index(drop=True), report


def get_preprocess_report(df: pd.DataFrame) -> dict:
    """返回缺失值、重复值、异常值统计。"""
    report: dict = {
        "总行数": len(df),
        "缺失值统计": df.isna().sum().to_dict(),
        "重复行数": int(df.duplicated().sum()),
    }
    if "Quantity" in df.columns:
        report["Quantity<=0行数"] = int((pd.to_numeric(df["Quantity"], errors="coerce") <= 0).sum())
    if "UnitPrice" in df.columns:
        report["UnitPrice<=0行数"] = int((pd.to_numeric(df["UnitPrice"], errors="coerce") <= 0).sum())
    if "InvoiceNo" in df.columns:
        report["退货记录行数"] = int(df["InvoiceNo"].astype(str).str.upper().str.startswith("C").sum())
    return report