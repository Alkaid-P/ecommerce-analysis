# pages/5_行为预测.py
import json

import numpy as np
import pandas as pd
import streamlit as st

from config import CLEANED_DATA_FILE, MODEL_DIR, USER_FEATURE_FILE
from src.data_loader import load_csv, load_uploaded_file
from src.feature_engineering import (
    build_churn_label,
    build_purchase_label,
    build_user_features,
    merge_features_and_labels,
)
from src.logger import log_operation
from src.prediction import (
    evaluate_model,
    get_models,
    predict_buy,
    predict_churn,
    save_model,
    split_data,
    train_model,
)
from src.utils import execute_sqlite
from src.visualization import plot_model_comparison


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.warning("请先登录")
        return
    st.caption(f"当前用户：{user['user_name']}（{user['role']}）")
    st.header("行为预测")

    task = st.selectbox("预测任务", ["购买预测", "流失预测"])
    task_key = "buy" if task == "购买预测" else "churn"
    label_col = "buy_label" if task_key == "buy" else "churn_label"

    try:
        if task_key == "buy":
            if not CLEANED_DATA_FILE.exists():
                st.warning("未找到清洗后数据，请先完成数据预处理。")
                return
            cleaned = load_csv(CLEANED_DATA_FILE)
            labels = build_purchase_label(cleaned)
            features = load_csv(USER_FEATURE_FILE) if USER_FEATURE_FILE.exists() else build_user_features(cleaned)
        else:
            if not USER_FEATURE_FILE.exists():
                st.warning("未找到用户特征表，请先完成数据预处理。")
                return
            features = load_csv(USER_FEATURE_FILE)
            labels = build_churn_label(features)

        data = merge_features_and_labels(features, labels, label_col)
    except Exception as exc:
        st.error(f"准备训练数据失败: {exc}")
        return

    if data.empty:
        st.warning("训练数据为空，无法训练模型。")
        return

    feature_cols = [
        col for col in data.select_dtypes(include=[np.number]).columns
        if col not in ["CustomerID", label_col, "Cluster"]
    ]
    if not feature_cols:
        st.error("没有可用数值特征。")
        return

    st.write("训练数据规模：", data.shape)
    st.write("特征列：", feature_cols)

    algorithm = st.selectbox("选择算法", list(get_models().keys()))
    use_smote = st.checkbox("使用SMOTE处理类别不平衡", value=False)

    if st.button("训练并评估模型"):
        try:
            X_train, X_test, y_train, y_test = split_data(data, feature_cols, label_col)
            model = train_model(X_train, y_train, algorithm, use_smote=use_smote)
            metrics = evaluate_model(model, X_test, y_test)
            model_path = MODEL_DIR / f"{task_key}_{algorithm.lower()}.pkl"
            save_model(model, model_path)
            execute_sqlite(
                """
                INSERT INTO sys_model_info
                (model_name, model_task, algorithm, model_file_path, train_param, eval_index, create_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{task_key}_{algorithm}",
                    task,
                    algorithm,
                    str(model_path),
                    json.dumps({"use_smote": use_smote, "features": feature_cols}, ensure_ascii=False),
                    json.dumps(metrics, ensure_ascii=False),
                    int(user["user_id"]),
                ),
            )
            st.session_state[f"{task_key}_model"] = model
            st.session_state[f"{task_key}_feature_cols"] = feature_cols
            st.success("模型训练完成并保存。")
            st.subheader("评估指标")
            st.dataframe(pd.DataFrame([metrics]), width="stretch")
            log_operation(int(user["user_id"]), "模型训练", f"{task}-{algorithm}训练完成")
        except Exception as exc:
            st.error(f"模型训练失败: {exc}")
            log_operation(int(user["user_id"]), "模型训练", f"{task}-{algorithm}训练失败", "失败", str(exc))

    if st.button("训练全部模型并对比"):
        try:
            X_train, X_test, y_train, y_test = split_data(data, feature_cols, label_col)
            results = {}
            for alg in get_models().keys():
                model = train_model(X_train, y_train, alg, use_smote=use_smote)
                results[alg] = evaluate_model(model, X_test, y_test)
            st.plotly_chart(plot_model_comparison(results), width="stretch")
            st.dataframe(pd.DataFrame(results).T, width="stretch")
        except Exception as exc:
            st.error(f"多模型对比失败: {exc}")

    st.subheader("预测与导出")
    model = st.session_state.get(f"{task_key}_model")
    trained_cols = st.session_state.get(f"{task_key}_feature_cols")
    if model is None or trained_cols is None:
        st.info("请先训练模型，然后进行预测。")
        return

    uploaded = st.file_uploader("上传待预测用户特征CSV", type=["csv"], key=f"upload_{task_key}")
    base = None
    if uploaded is not None:
        try:
            base = load_uploaded_file(uploaded)
        except Exception as exc:
            st.error(f"读取待预测文件失败: {exc}")
    else:
        if st.button("使用当前用户特征进行预测", key=f"current_{task_key}"):
            base = features.copy()

    if base is not None:
        missing = [col for col in trained_cols if col not in base.columns]
        if missing:
            st.error(f"待预测数据缺少特征列: {missing}")
            return
        X_pred = base[trained_cols].fillna(0)
        probs = predict_buy(model, X_pred) if task_key == "buy" else predict_churn(model, X_pred)
        result = base.copy()
        result["预测概率"] = probs
        result["预测结果"] = (np.array(probs) >= 0.5).astype(int)
        st.dataframe(result.head(100), width="stretch")
        st.download_button(
            "下载预测结果CSV",
            data=result.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{task_key}_prediction.csv",
            mime="text/csv",
        )
        log_operation(int(user["user_id"]), "模型预测", f"{task}生成预测结果{len(result)}条")