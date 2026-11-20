#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 GitHub Pages 站点：把 HTML 全书与 EPUB 一起放进 docs/。

用法：python3 script/build_site.py
产物：
  docs/index.html            网页版全书（单文件）
  docs/the-hidden-thread.epub 电子书
  docs/.nojekyll             关闭 Jekyll 处理
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
DOCS = os.path.join(ROOT, "docs")

HTML_SRC = os.path.join(OUT, "隐线-科技浪潮的底层逻辑.html")
EPUB_SRC = os.path.join(OUT, "隐线-科技浪潮的底层逻辑.epub")
EPUB_NAME = "the-hidden-thread.epub"


def run(script):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "script", script)], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"{script} 失败")


def main():
    run("build.py")
    run("build_epub.py")

    os.makedirs(DOCS, exist_ok=True)
    shutil.copyfile(HTML_SRC, os.path.join(DOCS, "index.html"))
    shutil.copyfile(EPUB_SRC, os.path.join(DOCS, EPUB_NAME))

    nojekyll = os.path.join(DOCS, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()

    for name in sorted(os.listdir(DOCS)):
        p = os.path.join(DOCS, name)
        if os.path.isfile(p):
            print(f"  docs/{name:28s} {os.path.getsize(p) // 1024:>5d} KB")


if __name__ == "__main__":
    main()
