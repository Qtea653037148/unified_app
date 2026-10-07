# AI 辅助评卷 · 统一入口

把 OCR 置信度分层、答案聚类、评分模型三个项目整合到一个 Streamlit 多页面应用。

## 在线演示

- **URL**: https://unbuckled-poking-treadmill.ngrok-free.dev

首次访问会看到 ngrok 警告页，点击 Visit Site 进入。侧边栏可切换三个页面。

## 包含的页面

| 页面 | 来源 | 内容 |
| --- | --- | --- |
| 📝 OCR 置信度分层 | 项目一 | 三模型对比 + 置信度分析 + 候选池导出 |
| 🎯 答案聚类与定标集 | 项目二 | UMAP 点云 + 聚类对比 + 定标集浏览 |
| 📊 OCR 复核优先级 | 项目三 | 待启动 |

## 相关项目

- **项目一**：[ocr_calibration_data](https://github.com/Qtea653037148/ocr_calibration_data)
- **项目二**：[answer_clustering_calibration_sampler](https://github.com/Qtea653037148/answer_clustering_calibration_sampler)
- **项目三**：规划中

## 架构

本仓库不复制子项目代码，只提供 Streamlit 多页面导航。

    用户 → https://xxx.ngrok-free.dev
             ↓
        unified_app (Streamlit 8501)
             ↓ 侧边栏选择
        ┌────────────┬────────────┬────────────┐
        │ 项目一页面 │ 项目二页面 │ 项目三页面 │
        └────────────┴────────────┴────────────┘
             ↓ sys.path 隔离
        ~/py_obj/ocr_calibration_data/
        ~/py_obj/answer_clustering_calibration_sampler/

## 前置条件

**两个子项目已经克隆到本地**：

    cd ~/py_obj
    git clone https://github.com/Qtea653037148/ocr_calibration_data.git
    git clone https://github.com/Qtea653037148/answer_clustering_calibration_sampler.git
    cd ocr_calibration_data && bash scripts/setup_links.sh 2>/dev/null || true

**注意**：`pages/` 里的文件是从子项目自动派生的，**不在 GitHub 上手工维护**。修改后运行 `regenerate.py` 重新生成。

## 项目结构

    unified_app/
    ├── app.py                              主入口（多页面导航）
    ├── regenerate.py                       从子项目自动生成页面
    ├── requirements.txt
    ├── README.md
    └── pages/
        ├── 01_ocr_calibration.py           [自动生成]
        ├── 02_clustering_sampler.py        [自动生成]
        └── 03_grading_model.py             项目三占位

## 快速开始

### 环境

    conda activate wsl_def
    pip install -r requirements.txt

### 步骤 1：克隆子项目

    cd ~/py_obj
    git clone https://github.com/Qtea653037148/ocr_calibration_data.git
    git clone https://github.com/Qtea653037148/answer_clustering_calibration_sampler.git

### 步骤 2：重新生成页面

    cd ~/py_obj/unified_app
    python regenerate.py

### 步骤 3：启动 Streamlit

    streamlit run app.py --server.port 8501

打开 http://localhost:8501

### 步骤 4（可选）：ngrok 公网访问

    ngrok http 8501

## 多项目共存的解决方案

**问题**：两个子项目都有自己的 `configs` 和 `src` 包。Python 的 `sys.modules` 是全局缓存，加载项目一后，`import configs` 会返回项目一的 configs，导致项目二报 `ImportError`。

**解决方案**：路径隔离 + 模块缓存清理。

在 `pages/*.py` 的顶部：

    import sys
    PROJECT_ROOT = "/path/to/project"

    # 1. 把当前项目路径放到 sys.path 最前
    while PROJECT_ROOT in sys.path:
        sys.path.remove(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

    # 2. 清空可能被其他项目占用的模块缓存
    for _mod in list(sys.modules.keys()):
        if _mod == "configs" or _mod.startswith("configs."):
            del sys.modules[_mod]
        if _mod == "src" or _mod.startswith("src."):
            del sys.modules[_mod]

**为什么必须清 src**：`src` 内部有 `from configs import ...`。如果 `src` 被缓存，它的内部 import 会一直引用**第一次加载时的 configs**。

## 技术栈

- Streamlit 1.36+ (st.navigation + st.Page)
- 两个子项目：PyTorch / PaddleOCR / Transformers / UMAP / HDBSCAN

## 开发说明

### 更新子项目后同步

当项目一或项目二更新了 `scripts/app.py`：

    cd ~/py_obj/unified_app
    python regenerate.py

### 添加项目三

1. 修改 `regenerate.py` 的 `PROJECTS` 列表，添加项目三的路径
2. 或者直接手工创建 `pages/03_grading_model.py`
3. 主入口 `app.py` 已经注册了 `03_grading_model.py` 的 `st.Page`

## License

MIT


---

## GitHub 生态

| 项目 | 说明 | 仓库 |
| --- | --- | --- |
| 📝 项目一 | OCR 置信度分层 | [ocr_calibration_data](https://github.com/Qtea653037148/ocr_calibration_data) |
| 🎯 项目二 | 答案聚类与定标集 | [answer_clustering_calibration_sampler](https://github.com/Qtea653037148/answer_clustering_calibration_sampler) |
| 📊 项目三 | OCR 复核优先级 | [ocr_review_prioritizer](https://github.com/Qtea653037148/ocr_review_prioritizer) |
| 🏠 统一入口 | 本项目 | [unified_app](https://github.com/Qtea653037148/unified_app) |

## 页面结构

- **🏠 项目总览**：三项目卡片 + 数据流 + 关键指标
- **📝 OCR 置信度分层**：三模型对比 + 置信度分析
- **🎯 答案聚类与定标集**：UMAP 点云 + 聚类对比 + 定标集
- **📊 OCR 复核优先级**：特征重要性 + 主动学习 + Top-K 召回
