# -*- coding: utf-8 -*-
"""
统一入口：AI 辅助评卷项目集

包含：
  - 项目一：OCR 置信度分层
  - 项目二：答案聚类与定标集筛选
  - 项目三：OCR 复核优先级

启动：
    cd ~/py_obj/unified_app
    conda activate wsl_def
    streamlit run app.py --server.address 0.0.0.0 --server.port 8501
"""
import streamlit as st

# ==================== 全局页面配置（只能调用一次） ====================
st.set_page_config(
    page_title="AI 辅助评卷 · 项目集",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 多页面导航 ====================
pg = st.navigation([
    st.Page(
        "pages/00_home.py",
        title="🏠 项目总览",
        icon="🏠",
        default=True,
    ),
    st.Page(
        "pages/01_ocr_calibration.py",
        title="📝 OCR 置信度分层",
        icon="📝",
    ),
    st.Page(
        "pages/02_clustering_sampler.py",
        title="🎯 答案聚类与定标集",
        icon="🎯",
    ),
    st.Page(
        "pages/03_grading_model.py",
        title="📊 OCR 复核优先级",
        icon="📊",
    ),
])

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### 🔗 GitHub 仓库")
    st.markdown("- [📝 项目一：OCR 分层](https://github.com/Qtea653037148/ocr_calibration_data)")
    st.markdown("- [🎯 项目二：聚类定标](https://github.com/Qtea653037148/answer_clustering_calibration_sampler)")
    st.markdown("- [📊 项目三：复核优先级](https://github.com/Qtea653037148/ocr_review_prioritizer)")
    st.markdown("- [🏠 unified_app（本仓库）](https://github.com/Qtea653037148/unified_app)")
    st.markdown("---")
    st.markdown("### 🌐 在线演示")
    st.markdown("[unified_app 入口](https://unbuckled-poking-treadmill.ngrok-free.dev)")
    st.markdown("---")
    st.caption("Streamlit 多页面应用 · 统一入口")


# ==================== 运行选中页面 ====================
pg.run()
