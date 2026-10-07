# -*- coding: utf-8 -*-
"""
首页：三个项目的总览

[AUTO-MAINTAINED] 这个文件是 unified_app 的入口首页，手动维护。
"""
import streamlit as st

# 不用 st.set_page_config，由 app.py 主入口处理

st.title("🎯 AI 辅助评卷系统")
st.markdown("##### 从 OCR 识别到评分模型，三个独立项目的完整链路")

st.markdown("---")

# ==================== 三个项目卡片 ====================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📝 项目一")
    st.markdown("**OCR 置信度分层**")
    st.markdown("""
    - 输入：9,715 条手写汉字 OCR 结果
    - 输出：226 条候选池
    - 关键发现：PaddleOCR 校准最好（ECE=0.0124）
    - 阈值 0.97 捕获 75% 错误
    """)
    st.metric("筛选效率", "97.7%", "9,715 → 226")
    st.markdown(
        "[🔗 GitHub](https://github.com/Qtea653037148/ocr_calibration_data)  ·  "
        "**→ 侧边栏切换到项目一页面**"
    )

with col2:
    st.markdown("### 🎯 项目二")
    st.markdown("**答案聚类与定标集**")
    st.markdown("""
    - 输入：226 条候选池
    - 输出：48 条定标集
    - 关键发现：数据无强簇结构
    - 混合采样：分层 + 边界 + 聚类
    """)
    st.metric("提炼效率", "78.8%", "226 → 48")
    st.markdown(
        "[🔗 GitHub](https://github.com/Qtea653037148/answer_clustering_calibration_sampler)  ·  "
        "**→ 侧边栏切换到项目二页面**"
    )

with col3:
    st.markdown("### 📊 项目三")
    st.markdown("**人工复核筛选**")
    st.markdown("""
    - 输入：9,715 条 OCR 结果
    - 输出：复核优先级排序
    - 3 特征模型 AUC-PR 0.851
    - Top-100 召回率 100%
    """)
    st.metric("复核效率", "14 倍", "复核前 100 条 = 全部错误")
    st.markdown(
        "[🔗 GitHub](https://github.com/Qtea653037148/ocr_review_prioritizer)  ·  "
        "**→ 侧边栏切换到项目三页面**"
    )

st.markdown("---")

# ==================== 数据流图 ====================
st.subheader("数据流")

st.markdown("""
    项目一：9,715 条 OCR 结果
        ↓ 置信度 < 0.97
    226 条候选池（减少 97.7%）
        ↓ 聚类 + 混合采样
    48 条定标集（减少 78.8%）
        ↓ 评分模型训练
    预测「需要复核概率」
        ↓ Top-K 排序
    复核前 100 条 → 捕获 100% 错误
""")

st.markdown("---")

# ==================== 最终成果 ====================
st.subheader("最终成果")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("原始 OCR 结果", "9,715", "条")
with col2:
    st.metric("定标集大小", "48", "条")
with col3:
    st.metric("Top-100 召回率", "100%", "捕获全部错误")
with col4:
    st.metric("复核效率提升", "14x", "vs 全量复核")

st.markdown("---")

# ==================== 技术栈 ====================
st.subheader("技术栈")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**深度学习 / NLP**")
    st.markdown("""
    - CRNNv2 / PaddleOCR / TrOCR 三模型
    - Sentence-Transformers 文本嵌入
    - UMAP 降维
    - HDBSCAN / K-Means 聚类
    """)

with col2:
    st.markdown("**工程 / 可视化**")
    st.markdown("""
    - FastAPI REST 接口
    - SQLite 数据库（29,145 条记录）
    - Streamlit 多页面应用
    - Plotly 交互式可视化
    """)

st.markdown("---")

# ==================== 快速导航 ====================
st.subheader("快速导航")
st.markdown("""
**使用侧边栏切换页面：**
- 📝 OCR 置信度分层
- 🎯 答案聚类与定标集
- 📊 人工复核筛选

**完整流程约 20 分钟可跑通**（含模型下载）。
""")

# ==================== 底部 ====================
st.markdown("---")
st.caption("""
三个项目独立成 GitHub 仓库，通过 unified_app 统一入口展示。

- [项目一](https://github.com/Qtea653037148/ocr_calibration_data) ·
  [项目二](https://github.com/Qtea653037148/answer_clustering_calibration_sampler) ·
  [项目三](https://github.com/Qtea653037148/ocr_review_prioritizer) ·
  [unified_app](https://github.com/Qtea653037148/unified_app)
""")
