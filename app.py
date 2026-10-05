# -*- coding: utf-8 -*-
"""
统一入口：AI 辅助评卷项目集

包含：
  - 项目一：OCR 置信度分层
  - 项目二：答案聚类与定标集筛选
  - 项目三：（开发中）评分模型与人机一致率

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
        title="📊 评分模型（开发中）",
        icon="📊",
    ),
])

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### 🔗 相关链接")
    st.markdown(
        "- [GitHub · 项目一](https://github.com/Qtea653037148/ocr_calibration_data)\n"
        "- [GitHub · 项目二](https://github.com/Qtea653037148/answer_clustering_calibration_sampler)\n"
    )
    st.markdown("---")
    st.caption("Streamlit 多页面应用 | 统一入口")

# ==================== 运行选中页面 ====================
pg.run()
