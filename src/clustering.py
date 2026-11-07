# src/clustering.py
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from config import RANDOM_STATE


def prepare_cluster_features(user_features: pd.DataFrame) -> pd.DataFrame:
    """选取聚类特征并标准化。"""
    cols = ["Frequency", "Monetary", "AvgOrderValue", "Recency"]
    existing = [col for col in cols if col in user_features.columns]
    if not existing:
        raise ValueError("用户特征表中没有可用于聚类的列")
    data = user_features[existing].copy().fillna(0)
    scaled = StandardScaler().fit_transform(data)
    return pd.DataFrame(scaled, columns=existing, index=user_features.index)


def elbow_method(X_scaled: np.ndarray, max_k: int = 10) -> list[float]:
    """返回不同K值的SSE列表。"""
    sse: list[float] = []
    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        model.fit(X_scaled)
        sse.append(float(model.inertia_))
    return sse


def train_kmeans(X_scaled: np.ndarray, k: int) -> tuple[KMeans, np.ndarray]:
    """训练K-Means并返回模型和标签。"""
    model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = model.fit_predict(X_scaled)
    return model, labels


def get_cluster_summary(user_features: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """统计各簇用户数及特征均值。"""
    data = user_features.copy()
    data["Cluster"] = labels
    return data.groupby("Cluster", as_index=False).agg(
        用户数=("CustomerID", "count"),
        平均Recency=("Recency", "mean"),
        平均Frequency=("Frequency", "mean"),
        平均Monetary=("Monetary", "mean"),
        平均订单金额=("AvgOrderValue", "mean"),
    )


def save_kmeans_model(model: KMeans, file_path: Path) -> None:
    """保存K-Means模型。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, file_path)


def load_kmeans_model(file_path: Path) -> KMeans:
    """加载K-Means模型。"""
    return joblib.load(file_path)