# -*- coding: utf-8 -*-
# [AUTO-GENERATED] 由 unified_app/regenerate.py 从子项目派生
# 源文件: /home/administratorscz/py_obj/answer_clustering_calibration_sampler/scripts/app.py
# 不要手动编辑本文件，改动请改原文件后重新生成

import os
import sys

# ============ 路径隔离（多项目共存必需） ============
PROJECT_ROOT = "/home/administratorscz/py_obj/answer_clustering_calibration_sampler"

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
项目二：答案聚类与定标集筛选 — Streamlit 面板

运行：
    streamlit run scripts/app.py --server.port 8502
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

from configs import (
    CANDIDATES_JSON, EMBEDDINGS_NPY, FIGURES_DIR, DATA_DIR,
    PROJECT_ONE_ROOT,
)

# ==================== 页面配置 ====================
# [unified_app] set_page_config 由主入口处理
# ==================== 数据加载 ====================
@st.cache_data(ttl=600)
def load_data():
    with open(CANDIDATES_JSON, encoding="utf-8") as f:
        candidates = json.load(f)
    embeddings = np.load(EMBEDDINGS_NPY)
    coords = np.load(os.path.join(FIGURES_DIR, "umap_2d.npy"))
    with open(os.path.join(DATA_DIR, "clusters.json"), encoding="utf-8") as f:
        clusters = json.load(f)
    with open(os.path.join(DATA_DIR, "calibration_set.json"), encoding="utf-8") as f:
        cal_set = json.load(f)
    return candidates, embeddings, coords, clusters, cal_set


def get_image_path(image_path):
    """从项目一找图片（项目二软链接过来或直接访问）"""
    # 尝试项目一的图片目录
    p1 = os.path.join(PROJECT_ONE_ROOT, "data", "images", image_path)
    if os.path.exists(p1):
        return p1
    # 备选：项目二的副本目录
    p2 = os.path.join(PROJECT_ROOT, "data", "candidates", image_path)
    if os.path.exists(p2):
        return p2
    return None


candidates, embeddings, coords, clusters_data, cal_set = load_data()

confs = np.array([c["confidence"] for c in candidates])
corrects = np.array([c["is_correct"] for c in candidates])
texts = [c["ocr_text"] for c in candidates]
targets = [c["target"] for c in candidates]

# 侧边栏
st.sidebar.title("🎯 定标集构建")
st.sidebar.markdown(f"""
**候选池**：{len(candidates)} 条
**定标集**：{len(cal_set)} 条
**嵌入维度**：{embeddings.shape[1]}
""")
st.sidebar.markdown("---")
st.sidebar.caption("项目一：[ocr_calibration_data](https://github.com/Qtea653037148/ocr_calibration_data)")
st.sidebar.caption("项目二：答案聚类与定标集")

st.title("🎯 答案聚类与定标集筛选")

# ==================== Tab ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 概览", "🗺️ UMAP 点云", "🔬 聚类对比",
    "⭐ 定标集", "📈 对比项目一",
])


# ============================================================
# Tab 1: 概览
# ============================================================
with tab1:
    st.subheader("候选池概览")
    st.markdown(f"""
    从**项目一**筛选出 **{len(candidates)} 条**困难样本：
    - 模型：PaddleOCR
    - 置信度 < 0.97
    - 全部识别错误或低置信度
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总样本数", len(candidates))
    with col2:
        n_correct = int(corrects.sum())
        st.metric("正确样本", f"{n_correct} ({n_correct/len(candidates)*100:.1f}%)")
    with col3:
        st.metric("平均置信度", f"{confs.mean():.4f}")
    with col4:
        st.metric("定标集大小", len(cal_set))

    st.markdown("---")
    st.subheader("置信度分布")

    fig = px.histogram(
        x=confs,
        nbins=40,
        labels={"x": "置信度", "y": "样本数"},
        title="候选池的置信度分布",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("编辑距离分布")
    ed_dist = pd.Series([c["edit_distance"] for c in candidates]).value_counts().sort_index()
    fig = px.bar(
        x=ed_dist.index, y=ed_dist.values,
        labels={"x": "编辑距离", "y": "样本数"},
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tab 2: UMAP 点云
# ============================================================
with tab2:
    st.subheader("UMAP 2D 投影")

    color_by = st.radio(
        "着色方式",
        ["置信度", "正确/错误", "簇标签（K-Means 8）", "定标集"],
        horizontal=True,
    )

    # 定标集索引集合
    cal_indices = {c["index"] for c in cal_set}

    fig = go.Figure()

    if color_by == "置信度":
        fig.add_trace(go.Scatter(
            x=coords[:, 0], y=coords[:, 1],
            mode="markers",
            marker=dict(
                size=10, color=confs, colorscale="RdYlGn",
                colorbar=dict(title="置信度"),
                line=dict(width=0.5, color="white"),
                opacity=0.85,
            ),
            text=[f"{texts[i]}→{targets[i]}<br>conf={confs[i]:.3f}"
                  for i in range(len(candidates))],
            hoverinfo="text",
        ))
    elif color_by == "正确/错误":
        for label, name, color in [(1, "正确", "#4CAF50"), (0, "错误", "#F44336")]:
            mask = corrects == label
            fig.add_trace(go.Scatter(
                x=coords[mask, 0], y=coords[mask, 1],
                mode="markers",
                marker=dict(size=10, color=color, opacity=0.75,
                            line=dict(width=0.5, color="white")),
                text=[f"{texts[i]}→{targets[i]}<br>conf={confs[i]:.3f}"
                      for i in np.where(mask)[0]],
                hoverinfo="text",
                name=name,
            ))
    elif "簇" in color_by:
        labels = np.array(clusters_data["algorithms"]["kmeans"]["labels"])
        unique = sorted(set(labels))
        palette = ["#2196F3", "#FF9800", "#9C27B0", "#4CAF50",
                   "#F44336", "#00BCD4", "#FFEB3B", "#795548"]
        for i, label in enumerate(unique):
            mask = labels == label
            fig.add_trace(go.Scatter(
                x=coords[mask, 0], y=coords[mask, 1],
                mode="markers",
                marker=dict(size=10, color=palette[i % len(palette)],
                            opacity=0.8, line=dict(width=0.5, color="white")),
                text=[f"簇 {label}<br>{texts[j]}→{targets[j]}"
                      for j in np.where(mask)[0]],
                hoverinfo="text",
                name=f"簇 {label} ({mask.sum()})",
            ))
    elif color_by == "定标集":
        is_sel = np.array([i in cal_indices for i in range(len(candidates))])
        # 未选
        fig.add_trace(go.Scatter(
            x=coords[~is_sel, 0], y=coords[~is_sel, 1],
            mode="markers",
            marker=dict(size=7, color="#CCCCCC", opacity=0.5),
            text=[texts[i] for i in np.where(~is_sel)[0]],
            hoverinfo="text",
            name=f"未选 ({int((~is_sel).sum())})",
        ))
        # 选中
        for is_correct, name, color in [(1, "定标集-正确", "#4CAF50"),
                                         (0, "定标集-错误", "#F44336")]:
            mask = is_sel & (corrects == is_correct)
            if mask.sum() == 0:
                continue
            fig.add_trace(go.Scatter(
                x=coords[mask, 0], y=coords[mask, 1],
                mode="markers",
                marker=dict(size=14, color=color, opacity=0.9,
                            line=dict(width=1.5, color="black")),
                text=[f"⭐ {texts[i]}→{targets[i]}<br>conf={confs[i]:.3f}"
                      for i in np.where(mask)[0]],
                hoverinfo="text",
                name=f"{name} ({int(mask.sum())})",
            ))

    fig.update_layout(
        height=650,
        xaxis_title="UMAP-1", yaxis_title="UMAP-2",
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tab 3: 聚类对比
# ============================================================
with tab3:
    st.subheader("三种聚类算法对比")

    # 指标表
    rows = []
    for algo in ["hdbscan", "kmeans", "agglomerative"]:
        m = clusters_data["algorithms"][algo]["metrics"]
        rows.append({
            "算法": algo,
            "簇数": m["n_clusters"],
            "噪声点": m["n_noise"],
            "轮廓系数": f"{m['silhouette']:.4f}" if m["silhouette"] else "N/A",
            "Davies-Bouldin": f"{m['davies_bouldin']:.4f}" if m["davies_bouldin"] else "N/A",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info("""
    **观察**：三种算法在 384 维原始嵌入上的轮廓系数都较低（<0.3），说明
    226 条样本在高维空间里没有明显簇结构。

    **在 UMAP-2D 上聚类效果更好**（轮廓系数 ~0.46），这也是我们最终
    使用 2D 聚类做采样辅助的原因。
    """)

    # 并排展示
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**384 维原始嵌入 — K-Means**")
        st.markdown("轮廓系数 ≈ 0.08（结构很弱）")
    with col2:
        st.markdown("**UMAP 2D 坐标 — K-Means K=6**")
        st.markdown("轮廓系数 ≈ 0.46（可用）")


# ============================================================
# Tab 4: 定标集
# ============================================================
with tab4:
    st.subheader(f"定标集（{len(cal_set)} 条）")
    st.markdown("""
    **用途**：交给专家组制定评分细则，训练 AI 评分模型。
    **来源**：分层采样（30）+ 边界采样（10）+ 聚类采样（10），去重后得到。
    """)

    # 统计
    col1, col2, col3, col4 = st.columns(4)
    sel_conf = [c["confidence"] for c in cal_set]
    n_correct = sum(c["is_correct"] for c in cal_set)
    with col1:
        st.metric("总条数", len(cal_set))
    with col2:
        st.metric("正确率", f"{n_correct/len(cal_set)*100:.1f}%")
    with col3:
        st.metric("置信度范围",
                  f"{min(sel_conf):.3f} ~ {max(sel_conf):.3f}")
    with col4:
        ed_dist = pd.Series([c["edit_distance"] for c in cal_set]).value_counts().to_dict()
        st.metric("编辑距离分布", str(ed_dist))

    st.markdown("---")
    st.markdown("**样本浏览**（每行 4 张）")

    # 图片网格
    n_cols = 4
    for i in range(0, len(cal_set), n_cols):
        cols = st.columns(n_cols)
        for j, col in enumerate(cols):
            if i + j >= len(cal_set):
                break
            item = cal_set[i + j]
            with col:
                img_path = get_image_path(item["image_path"])
                if img_path:
                    try:
                        img = Image.open(img_path)
                        st.image(img, use_container_width=True)
                    except Exception:
                        st.text("[图片加载失败]")
                else:
                    st.text("[图片不存在]")
                mark = "✓" if item["is_correct"] else "✗"
                st.markdown(
                    f"{mark} **识别**: `{item['ocr_text']}`  \n"
                    f"**目标**: `{item['target']}`  \n"
                    f"**conf**: `{item['confidence']:.4f}`  "
                    f"**ED**: `{item['edit_distance']}`"
                )

    st.markdown("---")
    # 导出
    export_json = json.dumps(cal_set, ensure_ascii=False, indent=2)
    st.download_button(
        label=f"📥 下载定标集 JSON（{len(cal_set)} 条）",
        data=export_json,
        file_name="calibration_set.json",
        mime="application/json",
    )


# ============================================================
# Tab 5: 对比项目一
# ============================================================
with tab5:
    st.subheader("项目一 vs 项目二")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 项目一：OCR 置信度分层")
        st.markdown("""
        **输入**：9,715 条 OCR 结果

        **动作**：置信度分层筛选

        **输出**：**226 条**候选池

        **核心发现**：
        - PaddleOCR 校准最好（ECE=0.0124）
        - 阈值 0.97 保留 97.7% 样本，捕获 75% 错误

        **数据资产**：
        - SQLite: 29,145 条
        - 4 张可视化图
        - REST API
        """)

    with col2:
        st.markdown("### 项目二：聚类与定标集")
        st.markdown(f"""
        **输入**：226 条候选池

        **动作**：聚类 + 混合采样

        **输出**：**{len(cal_set)} 条**定标集

        **核心工作**：
        - 文本嵌入（384 维）
        - UMAP 降维（384 → 2）
        - 三种聚类算法对比
        - 分层 + 边界 + 聚类混合采样

        **数据资产**：
        - 嵌入矩阵 (226, 384)
        - UMAP 2D 坐标
        - 聚类标签
        - 定标集 JSON
        """)

    st.markdown("---")
    st.subheader("数据流")
    st.markdown("""
9,715 条 OCR 结果
↓ 项目一：置信度 < 0.97
226 条候选池
↓ 项目二：聚类 + 采样
48 条定标集（最终交付）""")

st.success(f"""
**项目一筛选效率**：9,715 → 226（减少 97.7%）
**项目二进一步提炼**：226 → {len(cal_set)}（再减少 {100 - len(cal_set)/226*100:.1f}%）
**最终交付物**：{len(cal_set)} 条定标集，覆盖所有置信度区间和错误类型
""")


# ==================== 底部 ====================
st.sidebar.markdown("---")
st.sidebar.caption("💡 修改侧边栏设置，所有 Tab 会实时刷新")
