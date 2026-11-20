#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 EPUB 封面图（1600x2400），用无头 Chrome 渲染 HTML，保证与网页版视觉一致。

用法：python3 script/make_cover.py
输出：media/cover.png
"""

import os
import subprocess
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "media")
OUT = os.path.join(OUT_DIR, "cover.png")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1600, 2400

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<style>
@page{{margin:0}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:#f6f3ec}}
.sheet{{
  width:{W}px;height:{H}px;background:#fffdf8;position:relative;
  display:flex;flex-direction:column;justify-content:center;align-items:center;
  font-family:"Songti SC","Noto Serif SC",serif;color:#1c1a17;
}}
.mark{{font-family:"PingFang SC",sans-serif;font-size:22px;letter-spacing:16px;color:#8a8175;margin-bottom:130px;text-indent:16px}}
h1{{font-size:290px;font-weight:400;letter-spacing:52px;line-height:1.08;text-indent:52px}}
.sub{{font-size:62px;letter-spacing:16px;color:#4a453d;margin-top:80px;text-indent:16px}}
.rule{{width:150px;height:2px;background:#8c2f1e;margin:110px 0}}
.en{{font-family:"PingFang SC",sans-serif;font-size:26px;letter-spacing:8px;color:#8a8175;line-height:2.3;text-align:center}}
svg{{margin-top:150px}}
.author{{position:absolute;bottom:170px;font-family:"PingFang SC",sans-serif;font-size:30px;letter-spacing:14px;color:#4a453d}}
</style></head>
<body><div class="sheet">
  <div class="mark">非虚构的技术史</div>
  <h1>隐线</h1>
  <div class="sub">科技浪潮的底层逻辑</div>
  <div class="rule"></div>
  <div class="en">THE HIDDEN THREAD<br />THE UNDERLYING LOGIC OF TECHNOLOGICAL WAVES</div>
  <svg width="900" height="240" viewBox="0 0 560 150" fill="none">
    <path d="M10 30 H70 V46 H130 V62 H190 V78 H250 V94 H310 V110 H370 V126 H430 V138 H550"
          stroke="#1c1a17" stroke-width="1" opacity=".55"/>
    <g fill="#1c1a17" opacity=".8">
      <circle cx="70" cy="38" r="2.4"/><circle cx="130" cy="54" r="2.4"/>
      <circle cx="190" cy="70" r="2.4"/><circle cx="250" cy="86" r="2.4"/>
      <circle cx="310" cy="102" r="2.4"/><circle cx="370" cy="118" r="2.4"/>
      <circle cx="430" cy="132" r="2.4"/>
    </g>
  </svg>
  <div class="author">揖 光 尘</div>
</div></body></html>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="ht-cover-")
    html_path = os.path.join(tmpdir, "cover.html")
    png_path = os.path.join(tmpdir, "cover.png")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML.format(W=W, H=H))

    env = dict(os.environ)
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(k, None)

    cmd = [
        CHROME, "--headless=old", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--force-device-scale-factor=1",
        f"--window-size={W},{H}", "--virtual-time-budget=4000",
        f"--screenshot={png_path}", "file://" + html_path,
    ]
    subprocess.run(cmd, env=env, capture_output=True, timeout=120)

    if not os.path.exists(png_path):
        raise SystemExit("封面渲染失败")

    shutil.move(png_path, OUT)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("封面：", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
