#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 EPUB3 电子书：《隐线：科技浪潮的底层逻辑》

依赖：pandoc 3.x、media/cover.png（由 make_cover.py 生成）

用法：python3 script/build_epub.py
输出：output/隐线-科技浪潮的底层逻辑.epub
"""

import os
import re
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = os.path.join(ROOT, "draft")
OUT_DIR = os.path.join(ROOT, "output")
COVER = os.path.join(ROOT, "media", "cover.png")

BOOK_TITLE = "隐线"
BOOK_SUB = "科技浪潮的底层逻辑"
AUTHOR = "揖光尘"
LANG = "zh-CN"

# 与 build.py 的 ORDER 保持一致；(文件, 部名)
ORDER = [
    ("00-preface.md", None),
    ("00-intro.md", None),
    ("01-language.md", "第一部　从口到纸"),
    ("02-writing.md", "第一部　从口到纸"),
    ("03-bamboo-and-paper.md", "第一部　从口到纸"),
    ("04-print.md", "第一部　从口到纸"),
    ("05-telegraph.md", "第二部　电的速度"),
    ("06-telephone.md", "第二部　电的速度"),
    ("07-broadcast.md", "第二部　电的速度"),
    ("08-computer.md", "第三部　机器的加入"),
    ("09-internet.md", "第三部　机器的加入"),
    ("10-mobile.md", "第三部　机器的加入"),
    ("11-video.md", "第四部　理解的稀缺"),
    ("12-flood.md", "第四部　理解的稀缺"),
    ("13-ai.md", "第四部　理解的稀缺"),
    ("14-business.md", "第五部　两条横线"),
    ("15-capital.md", "第五部　两条横线"),
    ("98-closing.md", None),
    ("99-epilogue.md", None),
    ("A-timeline-and-references.md", None),
]

PART_SUB = {
    "第一部　从口到纸": "把话从空气里拿出来，钉在一个不会烂的东西上",
    "第二部　电的速度": "距离、门槛、人数——三堵墙依次拆掉",
    "第三部　机器的加入": "信息不再只被人搬运，开始被机器处理",
    "第四部　理解的稀缺": "当传、存、分发都免费了，唯一还贵的是懂",
    "第五部　两条横线": "竖着看是技术史，横着看是钱的历史",
}

CSS = """
@charset "utf-8";

html { -webkit-hyphens: auto; hyphens: auto; }

body {
  font-family: "Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", serif;
  font-size: 1em;
  line-height: 1.75;
  text-align: justify;
  margin: 0 0.4em;
}

p {
  margin: 0;
  text-indent: 2em;
  orphans: 2;
  widows: 2;
}

p + p { margin-top: 0.25em; }

h1, h2, h3 {
  font-family: "PingFang SC", "Noto Sans CJK SC", sans-serif;
  font-weight: 500;
  line-height: 1.45;
  text-indent: 0;
  page-break-after: avoid;
}

h1 {
  font-size: 1.5em;
  margin: 0 0 1.6em;
  padding-bottom: 0.5em;
  border-bottom: 1px solid #d8d0c1;
}

h2 {
  font-size: 1.14em;
  margin: 1.9em 0 0.8em;
  padding-left: 0.6em;
  border-left: 3px solid #8c2f1e;
}

h3 {
  font-size: 1em;
  margin: 1.5em 0 0.6em;
}

/* 部扉页 */
h1.part {
  border: 0;
  text-align: center;
  font-size: 1.7em;
  letter-spacing: 0.2em;
  margin: 35% 0 0.6em;
  padding: 0;
}
p.part-sub {
  text-align: center;
  text-indent: 0;
  font-family: "PingFang SC", sans-serif;
  font-size: 0.86em;
  letter-spacing: 0.16em;
  color: #6f6759;
  margin-bottom: 35%;
}

blockquote {
  margin: 1.3em 0;
  padding: 0.7em 1em;
  border-left: 3px solid #bdb3a1;
  background: #f7f3ea;
  font-size: 0.95em;
}
blockquote p { text-indent: 0; }

ul, ol { margin: 0.8em 0 0.8em 1.4em; padding: 0; }
li { margin: 0.3em 0; text-indent: 0; }

hr {
  border: 0;
  height: 1px;
  background: #d8d0c1;
  width: 30%;
  margin: 1.8em auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-family: "PingFang SC", sans-serif;
  font-size: 0.78em;
  line-height: 1.5;
  margin: 1.2em 0;
}
th, td {
  border: 1px solid #d8d0c1;
  padding: 0.35em 0.45em;
  text-align: left;
  vertical-align: top;
  text-indent: 0;
}
th { background: #f2ebdd; font-weight: 600; }

code {
  font-family: monospace;
  font-size: 0.9em;
  background: #f2ebdd;
  padding: 0 0.2em;
}

strong { font-weight: 700; }

/* 参考文献条目：不缩进，条目间留白 */
ol.references p { text-indent: 0; }
"""


def strip_chapter_number(title: str):
    """把「第一章　语言：…」变成「语言：…」，epub 里章号交给目录。"""
    return re.sub(r"^第[一二三四五六七八九十]+章[\s\u3000]*", "", title)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build_markdown():
    chunks = []
    last_part = None
    for fname, part in ORDER:
        path = os.path.join(DRAFT, fname)
        if not os.path.exists(path):
            print("缺少文件:", fname)
            continue
        text = read(path).strip()

        if part and part != last_part:
            last_part = part
            sub = PART_SUB.get(part, "")
            chunks.append(
                f'# {part} {{.part}}\n\n'
                f'[{sub}]{{.part-sub}}\n'
            )

        # 逐节处理：一级标题去掉章号，其余原样
        lines = text.split("\n")
        out = []
        for ln in lines:
            m = re.match(r"^#\s+(.*)$", ln)
            if m and part:
                out.append("# " + strip_chapter_number(m.group(1)))
            else:
                out.append(ln)
        chunks.append("\n".join(out) + "\n")

    return "\n\n".join(chunks)


def fix_metadata(epub_path):
    """给 content.opf 补上"副标题"（EPUB3 的 title-type refinement）。

    pandoc 只把主标题写进 dc:title，副标题仅出现在扉页上；
    补这一步之后，阅读器书架上显示的书名才是完整的。
    """
    import zipfile, shutil

    tmp = epub_path + ".tmp"
    with zipfile.ZipFile(epub_path, "r") as zin:
        infos = zin.infolist()
        data = {i.filename: zin.read(i.filename) for i in infos}

    opf_name = next(n for n in data if n.endswith("content.opf"))
    opf = data[opf_name].decode("utf-8")

    if "epub-subtitle-1" not in opf:
        sub_title = (
            '    <meta refines="#epub-title-1" property="title-type">main</meta>\n'
            f'    <dc:title id="epub-subtitle-1">{BOOK_SUB}</dc:title>\n'
            '    <meta refines="#epub-subtitle-1" property="title-type">subtitle</meta>\n'
        )
        opf = opf.replace(
            "</dc:title>\n",
            "</dc:title>\n" + sub_title,
            1,
        )
        data[opf_name] = opf.encode("utf-8")

    with zipfile.ZipFile(tmp, "w") as zout:
        for info in infos:
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = (
                zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED
            )
            zi.external_attr = info.external_attr
            zout.writestr(zi, data[info.filename])

    shutil.move(tmp, epub_path)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if not os.path.exists(COVER):
        raise SystemExit("缺少封面：先运行 python3 script/make_cover.py")

    tmpdir = tempfile.mkdtemp(prefix="ht-epub-")
    md_path = os.path.join(tmpdir, "book.md")
    css_path = os.path.join(tmpdir, "epub.css")
    out_path = os.path.join(OUT_DIR, "隐线-科技浪潮的底层逻辑.epub")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown())
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(CSS)

    cmd = [
        "pandoc", md_path,
        "-f", "markdown+pipe_tables+fenced_divs+bracketed_spans",
        "-t", "epub3",
        "-o", out_path,
        "--toc", "--toc-depth=1",
        "--split-level=1",
        "--epub-cover-image", COVER,
        "--css", css_path,
        "--metadata", f"title={BOOK_TITLE}",
        "--metadata", f"subtitle={BOOK_SUB}",
        "--metadata", f"author={AUTHOR}",
        "--metadata", f"lang={LANG}",
        "--metadata", "publisher=xquant-work / My-Books",
        "--metadata", "rights=© 揖光尘",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise SystemExit("pandoc 构建失败")

    fix_metadata(out_path)

    size = os.path.getsize(out_path)
    print(f"生成：{out_path}  {size // 1024} KB")
    print("临时目录：", tmpdir)


if __name__ == "__main__":
    main()
