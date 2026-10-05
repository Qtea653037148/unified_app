#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从子项目重新生成 pages/ 里的页面

用法：
    python regenerate.py

依赖：
    两个子项目已经克隆到 ~/py_obj/ 下：
      - ocr_calibration_data
      - answer_clustering_calibration_sampler
"""
import os
import re
import sys

HOME = os.path.expanduser("~")

PROJECTS = [
    {
        "name": "项目一：OCR 置信度分层",
        "src": f"{HOME}/py_obj/ocr_calibration_data/scripts/app.py",
        "dst": f"{HOME}/py_obj/unified_app/pages/01_ocr_calibration.py",
        "root": f"{HOME}/py_obj/ocr_calibration_data",
    },
    {
        "name": "项目二：答案聚类与定标集",
        "src": f"{HOME}/py_obj/answer_clustering_calibration_sampler/scripts/app.py",
        "dst": f"{HOME}/py_obj/unified_app/pages/02_clustering_sampler.py",
        "root": f"{HOME}/py_obj/answer_clustering_calibration_sampler",
    },
]

HEADER_TEMPLATE = '''# -*- coding: utf-8 -*-
# [AUTO-GENERATED] 由 unified_app/regenerate.py 从子项目派生
# 源文件: {src}
# 不要手动编辑本文件，改动请改原文件后重新生成

import os
import sys

# ============ 路径隔离（多项目共存必需） ============
PROJECT_ROOT = "{root}"

while PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

for _mod in list(sys.modules.keys()):
    if _mod == "configs" or _mod.startswith("configs."):
        del sys.modules[_mod]
    if _mod == "src" or _mod.startswith("src."):
        del sys.modules[_mod]
# ==================================================

'''


def generate_page(proj):
    src = proj["src"]
    dst = proj["dst"]
    root = proj["root"]

    if not os.path.exists(src):
        print(f"[SKIP] 源文件不存在: {src}")
        return False

    print(f"[{proj['name']}]")
    print(f"  源: {src}")

    with open(src, encoding="utf-8") as f:
        content = f.read()

    # 1. 移除原有的 PROJECT_ROOT 定义
    content = re.sub(
        r'PROJECT_ROOT\s*=\s*os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\s*\n',
        '',
        content,
    )
    # 2. 移除 sys.path.insert
    content = re.sub(
        r'sys\.path\.insert\(0,\s*PROJECT_ROOT\)\s*\n',
        '',
        content,
    )
    # 3. 移除 set_page_config
    content = re.sub(
        r'st\.set_page_config\s*\([^)]*\)\s*\n?',
        '# [unified_app] set_page_config 由主入口处理\n',
        content,
    )

    header = HEADER_TEMPLATE.format(src=src, root=root)
    content = header + content

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  目: {dst}")
    print(f"  大小: {len(content)} 字符")
    return True


def main():
    print("=" * 70)
    print("从子项目重新生成 unified_app/pages/")
    print("=" * 70)

    success = 0
    for proj in PROJECTS:
        if generate_page(proj):
            success += 1
        print()

    print(f"完成: {success}/{len(PROJECTS)}")
    print()
    print("提示：重启 Streamlit 让修改生效：")
    print("  pkill -f 'streamlit run'")
    print("  cd ~/py_obj/unified_app")
    print("  streamlit run app.py --server.port 8501")


if __name__ == "__main__":
    main()
