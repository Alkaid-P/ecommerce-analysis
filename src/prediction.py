# src/prediction.py
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from config import RANDOM_STATE, TEST_SIZE


def split_data(df: pd.DataFrame, feature_cols: list[str], label_col: str) -> tuple:
    """划分训练集和测试集。"""
    X = df[feature_cols].fillna(0)
    y = df[label_col].astype(int)
    stratify = y if y.value_counts().min() >= 2 else None
    return train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=stratify
    )


def apply_smote(X_train, y_train) -> tuple:
    """使用SMOTE对训练集过采样。"""
    smote = SMOTE(random_state=RANDOM_STATE)
    return smote.fit_resample(X_train, y_train)


def get_models() -> dict[str, Any]:
    """返回算法名称到模型实例的字典。"""
    return {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "DecisionTreeClassifier": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "RandomForestClassifier": RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=200),
        "SVC": SVC(probability=True, random_state=RANDOM_STATE),
        "XGBClassifier": XGBClassifier(
            random_state=RANDOM_STATE,
            eval_metric="logloss",
        ),
    }


def train_model(X_train, y_train, algorithm: str, use_smote: bool = False):
    """训练指定算法。"""
    models = get_models()
    if algorithm not in models:
        raise ValueError(f"不支持的算法: {algorithm}")
    model = models[algorithm]
    if use_smote:
        X_train, y_train = apply_smote(X_train, y_train)
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test) -> dict:
    """评估模型并返回指标。"""
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    else:
        y_prob = y_pred
    auc = float(roc_auc_score(y_test, y_prob)) if len(set(y_test)) > 1 else 0.0
    return {
        "Accuracy": float(accuracy_score(y_test, y_pred)),
        "Precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "Recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "F1": float(f1_score(y_test, y_pred, zero_division=0)),
        "AUC": auc,
    }


def save_model(model, file_path: Path) -> None:
    """保存模型。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, file_path)


def load_model(file_path: Path):
    """加载模型。"""
    return joblib.load(file_path)


def predict_buy(model, X: pd.DataFrame) -> np.ndarray:
    """返回购买概率。"""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.predict(X)


def predict_churn(model, X: pd.DataFrame) -> np.ndarray:
    """返回流失概率。"""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.predict(X)