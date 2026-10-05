# -*- coding: utf-8 -*-
# [AUTO-GENERATED] 由 unified_app/regenerate.py 从子项目派生
# 源文件: /home/administratorscz/py_obj/ocr_calibration_data/scripts/app.py
# 不要手动编辑本文件，改动请改原文件后重新生成

import os
import sys

# ============ 路径隔离（多项目共存必需） ============
PROJECT_ROOT = "/home/administratorscz/py_obj/ocr_calibration_data"

while PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

for _mod in list(sys.modules.keys()):
    if _mod == "configs" or _mod.startswith("configs."):
        del sys.modules[_mod]
    if _mod == "src" or _mod.startswith("src."):
        del sys.modules[_mod]
# ==================================================

# -*- coding: utf-8 -*-
"""
OCR 定标样本库 — Streamlit 可视化面板

运行：
    conda activate wsl_def
    cd ~/py_obj/ocr_calibration_data
    streamlit run scripts/app.py

浏览器打开：http://localhost:8501
"""
import os
import sys
import json
import sqlite3
from collections import defaultdict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# 让 streamlit 找到项目模块
from configs import DB_PATH, IMG_DIR, LOW_THRESHOLD, HIGH_THRESHOLD


# ==================== 页面配置 ====================
# [unified_app] set_page_config 由主入口处理
MODEL_LABELS = {"crnn": "CRNNv2", "paddle": "PaddleOCR", "trocr": "TrOCR"}
MODEL_COLORS = {"crnn": "#2196F3", "paddle": "#FF9800", "trocr": "#9C27B0"}


# ==================== 数据加载（缓存） ====================
@st.cache_data(ttl=600)
def load_data(db_path: str) -> pd.DataFrame:
    """加载全部 OCR 结果"""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT image_path, model_name, ocr_text, confidence,
               target, is_correct, edit_distance, latency_ms, error
        FROM ocr_results
        WHERE error IS NULL
    """, conn)
    conn.close()
    return df


# ==================== 错误捕获率 ====================
def compute_capture_curve(conf: np.ndarray, corr: np.ndarray,
                           thresholds: np.ndarray) -> dict:
    """对每个阈值 t，计算：
        - kept_ratio: 保留样本占比（conf >= t）
        - error_capture_rate: 保留样本中包含的错误占全部错误的比例
        - kept_error_rate: 保留样本的错误率
    """
    total_errors = int((corr == 0).sum())
    if total_errors == 0:
        return {"thresholds": thresholds.tolist(),
                "kept_ratio": [], "capture_rate": [], "kept_error_rate": []}

    kept_ratio, capture_rate, kept_error_rate = [], [], []
    for t in thresholds:
        kept = conf >= t
        kept_n = int(kept.sum())
        if kept_n == 0:
            kept_ratio.append(0.0)
            capture_rate.append(1.0)
            kept_error_rate.append(0.0)
            continue
        kept_errors = int((kept & (corr == 0)).sum())
        kept_ratio.append(kept_n / len(conf))
        # 保留样本中包含的错误占全部错误的比例
        capture_rate.append(kept_errors / total_errors)
        kept_error_rate.append(kept_errors / kept_n)

    return {
        "thresholds": thresholds.tolist(),
        "kept_ratio": kept_ratio,
        "capture_rate": capture_rate,
        "kept_error_rate": kept_error_rate,
    }


# ==================== 侧边栏 ====================
st.sidebar.title("⚙️ 控制面板")

df_all = load_data(DB_PATH)
all_models = sorted(df_all["model_name"].unique())

selected_models = st.sidebar.multiselect(
    "选择模型", all_models,
    default=all_models,
    format_func=lambda x: MODEL_LABELS.get(x, x),
)

if not selected_models:
    st.warning("请至少选择一个模型")
    st.stop()

df = df_all[df_all["model_name"].isin(selected_models)]

# 阈值（会随模型动态变化，暂时用全局默认）
st.sidebar.markdown("---")
st.sidebar.subheader("低置信度阈值")
default_low = LOW_THRESHOLD
low_threshold = st.sidebar.slider(
    "低于此值 → 待人工复核",
    min_value=0.0, max_value=1.0,
    value=float(default_low), step=0.01,
)
high_threshold = st.sidebar.slider(
    "高于此值 → 简单样本",
    min_value=0.0, max_value=1.0,
    value=float(HIGH_THRESHOLD), step=0.01,
)

st.sidebar.markdown("---")
st.sidebar.caption(f"数据库: `{DB_PATH}`")
st.sidebar.caption(f"总样本: {len(df_all)} 条")


# ==================== 标题 ====================
st.title("📝 OCR 定标样本库")
st.caption(f"数据来自 {DB_PATH}")


# ==================== Tab 布局 ====================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 概览", "🎯 错误捕获率", "🖼️ 样本浏览", "💾 候选池导出"]
)


# ============================================================
# Tab 1: 概览
# ============================================================
with tab1:
    st.subheader("模型核心指标")

    # 汇总表
    stats = []
    for m in selected_models:
        sub = df[df["model_name"] == m]
        n = len(sub)
        acc = sub["is_correct"].mean() if n > 0 else 0
        avg_conf = sub["confidence"].mean() if n > 0 else 0
        avg_ms = sub["latency_ms"].mean() if n > 0 else 0
        # ECE
        ece = 0.0
        n_bins = 15
        conf_arr = sub["confidence"].values
        corr_arr = sub["is_correct"].values
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        for i in range(n_bins):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            mask = (conf_arr > lo) & (conf_arr <= hi)
            if mask.sum() == 0:
                continue
            ece += (mask.sum() / n) * abs(conf_arr[mask].mean() - corr_arr[mask].mean())

        stats.append({
            "模型": MODEL_LABELS.get(m, m),
            "样本数": n,
            "准确率": f"{acc*100:.2f}%",
            "平均置信度": f"{avg_conf:.4f}",
            "ECE": f"{ece:.4f}",
            "平均耗时(ms)": f"{avg_ms:.1f}",
        })
    st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

    st.markdown("---")

    # 置信度分布
    st.subheader("置信度分布")
    col1, col2 = st.columns([1, 1])

    with col1:
        # 全部置信度直方图
        fig = go.Figure()
        for m in selected_models:
            sub = df[df["model_name"] == m]
            fig.add_trace(go.Histogram(
                x=sub["confidence"],
                name=MODEL_LABELS.get(m, m),
                marker_color=MODEL_COLORS.get(m, "#888"),
                opacity=0.6,
                nbinsx=80,
            ))
        fig.update_layout(
            barmode="overlay",
            xaxis_title="置信度",
            yaxis_title="样本数",
            height=400,
            xaxis=dict(range=[0.9, 1.0]),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 正确/错误分离
        fig = go.Figure()
        for m in selected_models:
            sub = df[df["model_name"] == m]
            for is_correct, label, dash in [(1, "正确", "solid"), (0, "错误", "dot")]:
                sub2 = sub[sub["is_correct"] == is_correct]
                if len(sub2) == 0:
                    continue
                fig.add_trace(go.Histogram(
                    x=sub2["confidence"],
                    name=f"{MODEL_LABELS.get(m, m)} {label}",
                    marker_color=MODEL_COLORS.get(m, "#888"),
                    opacity=0.5,
                    nbinsx=80,
                    histnorm="probability",
                ))
        fig.update_layout(
            barmode="overlay",
            xaxis_title="置信度",
            yaxis_title="概率密度",
            height=400,
            xaxis=dict(range=[0.9, 1.0]),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("三层分层统计")

    for m in selected_models:
        sub = df[df["model_name"] == m]
        n = len(sub)
        conf = sub["confidence"].values
        corr = sub["is_correct"].values

        low_mask = conf < low_threshold
        mid_mask = (conf >= low_threshold) & (conf <= high_threshold)
        high_mask = conf > high_threshold

        def layer_stats(mask, name, range_str):
            if mask.sum() == 0:
                return f"| {name} | {range_str} | 0 | 0.00% | — |"
            return (f"| {name} | {range_str} | {mask.sum()} | "
                    f"{mask.sum()/n*100:.2f}% | {corr[mask].mean()*100:.2f}% |")

        label = MODEL_LABELS.get(m, m)
        st.markdown(f"**{label}**")
        table = [
            "| 层 | 置信度区间 | 样本数 | 占比 | 层内准确率 |",
            "|---|---|---|---|---|",
            layer_stats(low_mask, "低置信", f"[0, {low_threshold})"),
            layer_stats(mid_mask, "中置信", f"[{low_threshold}, {high_threshold}]"),
            layer_stats(high_mask, "高置信", f"({high_threshold}, 1]"),
        ]
        st.markdown("\n".join(table))


# ============================================================
# Tab 2: 错误捕获率
# ============================================================
with tab2:
    st.subheader("错误捕获率曲线")
    st.markdown("""
    **问题**：如果用置信度筛选低质量样本，能捕获多少错误？

    **指标解释**：
    - **保留样本占比**：阈值 t 时，剩余多少比例的样本
    - **错误捕获率**：保留样本中包含的错误占全部错误的比例（越高越好）
    - **保留样本错误率**：保留样本中错误的比例（越高越好，说明富集了困难样本）
    """)

    thresholds = np.linspace(0.5, 0.999, 200)

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = go.Figure()
        for m in selected_models:
            sub = df[df["model_name"] == m]
            curve = compute_capture_curve(sub["confidence"].values,
                                           sub["is_correct"].values,
                                           thresholds)
            fig.add_trace(go.Scatter(
                x=curve["thresholds"],
                y=[v * 100 for v in curve["capture_rate"]],
                name=MODEL_LABELS.get(m, m),
                line=dict(color=MODEL_COLORS.get(m, "#888"), width=2),
            ))
        fig.update_layout(
            xaxis_title="置信度阈值 t",
            yaxis_title="错误捕获率 (%)",
            height=400,
            yaxis=dict(range=[0, 105]),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        for m in selected_models:
            sub = df[df["model_name"] == m]
            curve = compute_capture_curve(sub["confidence"].values,
                                           sub["is_correct"].values,
                                           thresholds)
            fig.add_trace(go.Scatter(
                x=curve["thresholds"],
                y=[v * 100 for v in curve["kept_ratio"]],
                name=MODEL_LABELS.get(m, m),
                line=dict(color=MODEL_COLORS.get(m, "#888"), width=2),
            ))
        fig.update_layout(
            xaxis_title="置信度阈值 t",
            yaxis_title="保留样本占比 (%)",
            height=400,
            yaxis=dict(range=[0, 105]),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("特定阈值下的富集分析")

    for m in selected_models:
        sub = df[df["model_name"] == m]
        conf = sub["confidence"].values
        corr = sub["is_correct"].values
        total_errors = int((corr == 0).sum())

        st.markdown(f"**{MODEL_LABELS.get(m, m)}**（总错误 {total_errors} 条）")
        rows = []
        for t in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 0.99]:
            kept = conf >= t
            kept_n = int(kept.sum())
            if kept_n == 0:
                continue
            kept_errors = int((kept & (corr == 0)).sum())
            rows.append({
                "阈值 t": f"{t:.2f}",
                "保留样本数": kept_n,
                "保留占比": f"{kept_n/len(conf)*100:.2f}%",
                "捕获错误数": kept_errors,
                "错误捕获率": f"{kept_errors/total_errors*100:.1f}%" if total_errors else "—",
                "保留样本错误率": f"{kept_errors/kept_n*100:.2f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ============================================================
# Tab 3: 样本浏览
# ============================================================
with tab3:
    st.subheader("样本浏览")

    # 筛选控件
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        browse_model = st.selectbox(
            "模型", selected_models,
            format_func=lambda x: MODEL_LABELS.get(x, x),
        )
    with col2:
        filter_type = st.selectbox(
            "筛选类型",
            ["全部", "低置信度", "中置信度", "高置信度", "仅错误"],
        )
    with col3:
        sort_by = st.selectbox("排序", ["置信度升序", "置信度降序"])
    with col4:
        page_size = st.selectbox("每页", [12, 24, 48, 96], index=1)

    # 应用筛选
    sub = df[df["model_name"] == browse_model].copy()

    if filter_type == "低置信度":
        sub = sub[sub["confidence"] < low_threshold]
    elif filter_type == "中置信度":
        sub = sub[(sub["confidence"] >= low_threshold) &
                   (sub["confidence"] <= high_threshold)]
    elif filter_type == "高置信度":
        sub = sub[sub["confidence"] > high_threshold]
    elif filter_type == "仅错误":
        sub = sub[sub["is_correct"] == 0]

    sub = sub.sort_values("confidence",
                           ascending=(sort_by == "置信度升序"))
    sub = sub.reset_index(drop=True)

    st.caption(f"共 {len(sub)} 条样本")

    if len(sub) == 0:
        st.info("没有符合条件的样本")
    else:
        # 分页
        max_page = (len(sub) - 1) // page_size + 1
        if max_page > 1:
            page = st.slider("页码", 1, max_page, 1)
        else:
            page = 1
        start = (page - 1) * page_size
        end = start + page_size
        page_df = sub.iloc[start:end]

        # 图片网格（每行 4 张）
        n_cols = 4
        for i in range(0, len(page_df), n_cols):
            cols = st.columns(n_cols)
            for j, col in enumerate(cols):
                if i + j >= len(page_df):
                    break
                row = page_df.iloc[i + j]
                img_path = os.path.join(IMG_DIR, row["image_path"])

                with col:
                    if os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            st.image(img, use_container_width=True)
                        except Exception:
                            st.text("[图片加载失败]")
                    else:
                        st.text("[图片不存在]")

                    # 状态标记
                    if row["is_correct"]:
                        status = "✅"
                    else:
                        status = "❌"

                    st.markdown(
                        f"{status} **置信度**: `{row['confidence']:.4f}`  \n"
                        f"**识别**: `{row['ocr_text']}`  \n"
                        f"**目标**: `{row['target']}`  \n"
                        f"**编辑距离**: {row['edit_distance']}"
                    )


# ============================================================
# Tab 4: 候选池导出
# ============================================================
with tab4:
    st.subheader("候选池导出")
    st.markdown("""
    为**项目二（聚类与定标集筛选）**准备候选样本。

    默认策略（基于置信度分析报告的结论）：
    - 取 **PaddleOCR** 置信度 **< 0.97** 的样本
    - 或 **三模型预测不一致**的样本
    """)

    # 选择主模型
    primary_model = st.selectbox(
        "主模型", selected_models,
        index=selected_models.index("paddle") if "paddle" in selected_models else 0,
        format_func=lambda x: MODEL_LABELS.get(x, x),
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        export_max_conf = st.slider(
            "候选池置信度上限", 0.5, 1.0, 0.97, 0.01,
            help="只导出置信度低于此值的样本",
        )
    with col2:
        export_mode = st.radio(
            "导出模式",
            ["置信度 < 上限", "置信度 < 上限 + 三模型不一致"],
            horizontal=False,
        )

    # 计算候选池
    primary = df[df["model_name"] == primary_model]
    candidates = primary[primary["confidence"] < export_max_conf].copy()

    # 三模型不一致检测
    if "不一致" in export_mode and len(selected_models) >= 2:
        pivot = df.pivot_table(
            index="image_path", columns="model_name",
            values="ocr_text", aggfunc="first"
        )
        # 判断每行有多少不同预测
        pivot["n_unique"] = pivot[selected_models].nunique(axis=1)
        inconsistent = pivot[pivot["n_unique"] > 1].index.tolist()
        inconsistent_set = set(inconsistent)
        extra = df[
            (df["model_name"] == primary_model) &
            (df["image_path"].isin(inconsistent_set)) &
            (df["confidence"] >= export_max_conf)
        ]
        candidates = pd.concat([candidates, extra]).drop_duplicates("image_path")

    candidates = candidates.reset_index(drop=True)

    st.markdown(f"**候选池大小**: {len(candidates)} 条")

    if len(candidates) > 0:
        st.dataframe(
            candidates[["image_path", "ocr_text", "confidence", "target", "is_correct"]]
            .head(50),
            use_container_width=True,
            hide_index=True,
        )

        # 导出
        export_data = candidates[[
            "image_path", "ocr_text", "confidence", "target", "is_correct"
        ]].to_dict(orient="records")
        export_json = json.dumps(export_data, ensure_ascii=False, indent=2)

        st.download_button(
            label=f"📥 下载候选池 ({len(candidates)} 条 JSON)",
            data=export_json,
            file_name=f"candidates_{primary_model}.json",
            mime="application/json",
        )


# ==================== 底部 ====================
st.sidebar.markdown("---")
st.sidebar.caption("💡 提示：修改侧边栏设置，所有 Tab 会实时刷新")
