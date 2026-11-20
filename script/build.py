#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《隐线：科技浪潮的底层逻辑》构建脚本
把 draft/*.md 拼成一本单文件 HTML（可打印）与一份合并 Markdown。

用法： python3 script/build.py
"""

import os
import re
import html
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = os.path.join(ROOT, "draft")
OUT = os.path.join(ROOT, "output")

BOOK_TITLE = "隐线"
BOOK_SUB = "科技浪潮的底层逻辑"
EPUB_FILE = "the-hidden-thread.epub"   # 与文档同目录时的文件名
BOOK_EN = "The Hidden Thread"
BOOK_EN_SUB = "The Logic of Technological Development"
AUTHOR = "揖光尘"

# (文件, 所属部)  part=None 表示前置/后置
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


# ---------------- Markdown 转换 ----------------

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def md_to_html(text):
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()

        if not s:
            i += 1
            continue

        # 表格
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = []
            for r in rows:
                if re.match(r"^\|[\s:\-\|]+\|$", r):
                    continue
                parts = [c.strip() for c in r.strip("|").split("|")]
                cells.append(parts)
            if cells:
                head, body = cells[0], cells[1:]
                out.append("<div class=\"table-wrap\"><table>")
                out.append("<thead><tr>" + "".join(
                    f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
                out.append("<tbody>")
                for row in body:
                    out.append("<tr>" + "".join(
                        f"<td>{inline(c)}</td>" for c in row) + "</tr>")
                out.append("</tbody></table></div>")
            continue

        # 分隔线
        if re.match(r"^---+$", s):
            out.append("<hr />")
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2)
            # 章节标题：拆“第一章　标题”
            anchor = "h" + str(abs(hash(txt)) % 1000000)
            out.append(f"<h{lvl} id=\"{anchor}\">{inline(txt)}</h{lvl}>")
            i += 1
            continue

        # 引用
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            paras = [p for p in buf if p]
            inner = "".join(f"<p>{inline(p)}</p>" for p in paras)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # 有序列表
        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue

        # 无序列表
        if re.match(r"^-\s+", s):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                items.append(re.sub(r"^-\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue

        # 段落
        buf = []
        while i < n:
            s2 = lines[i].strip()
            if not s2:
                break
            if s2.startswith("|") or s2.startswith(">") or re.match(r"^#{1,6}\s", s2) \
                    or re.match(r"^\d+\.\s+", s2) or re.match(r"^-\s+", s2) or re.match(r"^---+$", s2):
                break
            buf.append(s2)
            i += 1
        out.append("<p>" + inline("".join(buf)) + "</p>")

    return "\n".join(out)


def cn_quotes(text):
    """把成对的 ASCII 双引号换成中文弯引号 “ ”（按出现顺序交替）。"""
    out = []
    open_next = True
    for ch in text:
        if ch == '"':
            out.append("\u201c" if open_next else "\u201d")
            open_next = not open_next
        else:
            out.append(ch)
    return "".join(out)


def split_sections(path):
    """按一级标题切分，返回 [(title, html)]"""
    with open(path, encoding="utf-8") as f:
        text = cn_quotes(f.read())
    chunks = re.split(r"^#\s+", text, flags=re.M)
    secs = []
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue
        first, _, rest = ch.partition("\n")
        secs.append((first.strip(), md_to_html(rest)))
    return secs


# ---------------- 构建 ----------------

def build():
    os.makedirs(OUT, exist_ok=True)

    docs = []   # (part_or_None, title, html)
    for fname, part in ORDER:
        p = os.path.join(DRAFT, fname)
        if not os.path.exists(p):
            print("缺少文件:", fname)
            continue
        for title, body in split_sections(p):
            disp = re.sub(r"^第[一二三四五六七八九十]+章[\s\u3000]*", "", title) if part else title
            docs.append({"part": part, "title": title, "disp": disp, "html": body})

    # 目录
    toc_items = []
    chapters = []
    last_part = None
    seq = 0
    for idx, d in enumerate(docs):
        if d["part"] and d["part"] != last_part:
            last_part = d["part"]
            toc_items.append(
                f'<li class="toc-part">{html.escape(last_part)}</li>')
        num = ""
        if d["part"]:
            seq += 1
            num = f'<span class="toc-num">{seq:02d}</span>'
        toc_items.append(
            f'<li class="toc-chap"><a href="#ch{idx}">{num}'
            f'<span>{html.escape(d["disp"])}</span></a></li>')

    # 正文
    last_part = None
    seq = 0
    for idx, d in enumerate(docs):
        if d["part"] and d["part"] != last_part:
            last_part = d["part"]
            sub = PART_SUB.get(last_part, "")
            chapters.append(
                f'<section class="part-page">'
                f'<div class="part-inner"><div class="part-rule"></div>'
                f'<h2 class="part-name">{html.escape(last_part)}</h2>'
                f'<p class="part-sub">{html.escape(sub)}</p>'
                f'<div class="part-rule"></div></div></section>')
        kicker = ""
        if d["part"]:
            seq += 1
            kicker = f'<div class="chap-kicker">{html.escape(d["part"])}</div>'
        chapters.append(
            f'<article class="chapter" id="ch{idx}">'
            f'<header class="chap-head">{kicker}'
            f'<h1>{html.escape(d["disp"])}</h1></header>'
            f'<div class="chap-body">{d["html"]}</div></article>')

    today = datetime.date.today().isoformat()
    total_chars = sum(len(re.sub(r"<[^>]+>", "", d["html"])) for d in docs)

    tmpl = TEMPLATE
    out_html = (tmpl
                .replace("__EPUB__", EPUB_FILE)
                .replace("__TOC__", "\n".join(toc_items))
                .replace("__BODY__", "\n".join(chapters))
                .replace("__DATE__", today)
                .replace("__CHARS__", f"{total_chars // 1000}"))

    out_path = os.path.join(OUT, "隐线-科技浪潮的底层逻辑.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_html)

    # 合并 Markdown
    md_parts = [f"# {BOOK_TITLE}：{BOOK_SUB}\n\n**{BOOK_EN}: {BOOK_EN_SUB}**\n\n"]
    for d in docs:
        md_parts.append(f"# {d['title']}\n\n{d['html']}\n\n")
    with open(os.path.join(OUT, "隐线-科技浪潮的底层逻辑.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md_parts))

    print(f"生成：{out_path}")
    print(f"章节数：{len(docs)}　正文约 {total_chars // 1000} 千字")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="paper">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>隐线：科技浪潮的底层逻辑</title>
<style>
:root{
  --bg:#f6f3ec; --paper:#fffdf8; --ink:#1c1a17; --ink-2:#4a453d; --ink-3:#8a8175;
  --rule:#ddd5c6; --accent:#8c2f1e; --accent-soft:#f0e2d8;
  --serif:"Songti SC","Noto Serif SC","Source Han Serif SC",Georgia,"Times New Roman",serif;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",-apple-system,sans-serif;
}
html[data-theme="night"]{
  --bg:#14161a; --paper:#1b1e23; --ink:#e8e4dc; --ink-2:#b6b0a5; --ink-3:#7d766b;
  --rule:#33373e; --accent:#d98570; --accent-soft:#2a2320;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--serif); font-size:17px; line-height:1.95;
  -webkit-font-smoothing:antialiased;
}
#bar{position:fixed;top:0;left:0;height:3px;background:var(--accent);width:0;z-index:99}

/* 封面 */
.cover{
  min-height:100vh; display:flex; flex-direction:column; justify-content:center;
  align-items:center; padding:8vh 8vw; position:relative; text-align:center;
  background:var(--paper);
}
.cover-mark{font-family:var(--sans);font-size:11px;letter-spacing:.42em;color:var(--ink-3);margin-bottom:5vh}
.cover h1{
  font-size:clamp(60px,13vw,132px); margin:0; letter-spacing:.16em;
  font-weight:400; line-height:1.1; text-indent:.16em;
}
.cover .cn-sub{
  font-size:clamp(16px,2.1vw,25px); letter-spacing:.24em; color:var(--ink-2);
  margin:3.2vh 0 0; text-indent:.24em;
}
.cover .rule{width:64px;height:1px;background:var(--accent);margin:5vh 0}
.cover .en{font-family:var(--sans);font-size:12px;letter-spacing:.28em;color:var(--ink-3);line-height:2.2;max-width:min(640px,84vw)}
.cover svg{width:min(560px,84vw);margin:7vh 0 0;overflow:visible}
.cover .author{position:absolute;bottom:6vh;font-family:var(--sans);font-size:13px;letter-spacing:.3em;color:var(--ink-2)}
.cover .date{position:absolute;bottom:3.6vh;font-family:var(--sans);font-size:10px;letter-spacing:.2em;color:var(--ink-3)}

/* 目录 */
.toc-wrap{background:var(--paper);padding:14vh 8vw 16vh;border-top:1px solid var(--rule)}
.toc-inner{max-width:760px;margin:0 auto}
.toc-wrap h2{
  font-size:13px;font-family:var(--sans);letter-spacing:.34em;color:var(--ink-3);
  font-weight:400;margin:0 0 6vh;text-align:center
}
.toc{list-style:none;padding:0;margin:0}
.toc-part{
  font-family:var(--sans);font-size:12px;letter-spacing:.24em;color:var(--accent);
  margin:4.4vh 0 1.6vh;padding-bottom:.9vh;border-bottom:1px solid var(--rule)
}
.toc-part:first-child{margin-top:0}
.toc-chap a{
  display:flex;gap:14px;align-items:baseline;text-decoration:none;color:var(--ink);
  padding:.85vh 0;border-bottom:1px dotted transparent;transition:.2s
}
.toc-chap a:hover{color:var(--accent);border-bottom-color:var(--rule)}
.toc-num{font-family:var(--sans);font-size:11px;color:var(--ink-3);min-width:26px;letter-spacing:.1em}
.toc-chap span{font-size:16.5px}

/* 部扉页 */
.part-page{
  min-height:88vh;display:flex;align-items:center;justify-content:center;
  background:var(--paper);padding:10vh 8vw;border-top:1px solid var(--rule)
}
.part-inner{text-align:center;max-width:640px}
.part-name{
  font-size:clamp(26px,4vw,40px);font-weight:400;letter-spacing:.2em;
  margin:4vh 0;color:var(--ink);text-indent:.2em
}
.part-sub{font-size:15px;color:var(--ink-3);letter-spacing:.16em;margin:0}
.part-rule{width:40px;height:1px;background:var(--rule);margin:0 auto}

/* 章节 */
.chapter{
  background:var(--paper);padding:12vh 8vw 14vh;
  border-top:1px solid var(--rule);max-width:100%
}
.chap-head{max-width:700px;margin:0 auto 7vh;text-align:left}
.chap-kicker{
  font-family:var(--sans);font-size:11px;letter-spacing:.34em;color:var(--accent);margin-bottom:2.4vh
}
.chap-head h1{
  font-size:clamp(26px,3.6vw,38px);font-weight:400;line-height:1.5;
  margin:0;letter-spacing:.04em
}
.chap-body{max-width:700px;margin:0 auto}
.chap-body p{margin:0 0 1.55em;text-align:justify;text-justify:inter-ideograph}
.chap-body p:first-of-type::first-letter{font-size:1em}

.chap-body h2{
  font-size:20px;font-weight:400;letter-spacing:.1em;margin:3.4em 0 1.2em;
  padding-left:14px;border-left:2px solid var(--accent);line-height:1.6
}
.chap-body h3{font-size:17px;font-weight:600;margin:2.4em 0 .9em;letter-spacing:.04em}

.chap-body blockquote{
  margin:2.4em 0;padding:1.4em 1.8em;background:var(--accent-soft);
  border-left:2px solid var(--accent);color:var(--ink);
  font-size:16px;border-radius:2px
}
.chap-body blockquote p{margin:0 0 .6em}
.chap-body blockquote p:last-child{margin-bottom:0}

.chap-body ul,.chap-body ol{margin:0 0 1.6em;padding-left:1.5em}
.chap-body li{margin:.4em 0;text-align:justify}

.chap-body hr{border:0;height:1px;background:var(--rule);margin:3.2em auto;width:38%}

.chap-body strong{font-weight:700;color:var(--ink)}
.chap-body code{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;
  background:var(--accent-soft);padding:.1em .4em;border-radius:2px
}

.table-wrap{overflow-x:auto;margin:2.2em 0 2.6em;border:1px solid var(--rule);border-radius:2px}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-family:var(--sans);line-height:1.7}
th,td{padding:8px 11px;text-align:left;border-bottom:1px solid var(--rule);vertical-align:top}
th{background:var(--accent-soft);font-weight:600;color:var(--ink);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:rgba(140,47,30,.04)}

.colophon{
  background:var(--paper);padding:16vh 8vw;text-align:center;border-top:1px solid var(--rule)
}
.colophon p{font-family:var(--sans);font-size:11px;letter-spacing:.26em;color:var(--ink-3);line-height:2.6;margin:0}
.colophon a.dl{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent);padding-bottom:1px}

/* 工具 */
#tools{position:fixed;right:20px;bottom:20px;display:flex;flex-direction:column;gap:8px;z-index:60}
#tools button,#tools a{
  width:38px;height:38px;border-radius:50%;border:1px solid var(--rule);
  background:var(--paper);color:var(--ink-2);cursor:pointer;font-size:13px;
  font-family:var(--sans);display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 10px rgba(0,0,0,.06);transition:.2s;text-decoration:none
}
#tools button:hover,#tools a:hover{color:var(--accent);border-color:var(--accent)}
@media(max-width:640px){
  body{font-size:16px}
  .cover .en{font-size:10.5px;letter-spacing:.16em;line-height:2.4}
  .chapter,.toc-wrap{padding-left:6vw;padding-right:6vw}
  .chap-body p{text-align:left}
}

@media print{
  :root{--bg:#fff;--paper:#fff}
  #tools,#bar,.colophon a.dl{display:none}
  body{font-size:11.5pt;line-height:1.85}
  .cover{min-height:100vh;page-break-after:always;border:0}
  .toc-wrap{page-break-after:always;border-top:0}
  .part-page{page-break-before:always;min-height:auto;height:100vh;border:0}
  .chapter{page-break-before:always;border-top:0;padding:0 0 2em}
  .chap-head h1{font-size:20pt}
  .chap-body h2{font-size:13pt}
  .chap-body blockquote{background:#faf6ef}
  table{font-size:8.5pt}
  .colophon{page-break-before:always}
  @page{margin:18mm 16mm}
}
</style>
</head>
<body>
<div id="bar"></div>

<section class="cover">
  <div class="cover-mark">非 虚 构 的 技 术 史</div>
  <h1>隐线</h1>
  <p class="cn-sub">科技浪潮的底层逻辑</p>
  <div class="rule"></div>
  <div class="en">THE HIDDEN THREAD<br />THE UNDERLYING LOGIC OF TECHNOLOGICAL WAVES</div>

  <svg viewBox="0 0 560 150" fill="none" aria-hidden="true">
    <path d="M10 30 H70 V46 H130 V62 H190 V78 H250 V94 H310 V110 H370 V126 H430 V138 H550"
          stroke="currentColor" stroke-width="1" opacity=".55" />
    <g fill="currentColor" opacity=".8">
      <circle cx="70" cy="38" r="2.6"/><circle cx="130" cy="54" r="2.6"/>
      <circle cx="190" cy="70" r="2.6"/><circle cx="250" cy="86" r="2.6"/>
      <circle cx="310" cy="102" r="2.6"/><circle cx="370" cy="118" r="2.6"/>
      <circle cx="430" cy="132" r="2.6"/>
    </g>
    <text x="70" y="20" font-size="9" fill="currentColor" opacity=".5" text-anchor="middle" style="font-family:var(--sans)">语言</text>
    <text x="190" y="52" font-size="9" fill="currentColor" opacity=".5" text-anchor="middle" style="font-family:var(--sans)">纸</text>
    <text x="310" y="84" font-size="9" fill="currentColor" opacity=".5" text-anchor="middle" style="font-family:var(--sans)">电报</text>
    <text x="430" y="114" font-size="9" fill="currentColor" opacity=".5" text-anchor="middle" style="font-family:var(--sans)">互联网</text>
    <text x="540" y="128" font-size="9" fill="currentColor" opacity=".5" text-anchor="middle" style="font-family:var(--sans)">AI</text>
  </svg>

  <div class="author">揖 光 尘</div>
  <div class="date">__DATE__</div>
</section>

<section class="toc-wrap">
  <div class="toc-inner">
    <h2>目 录</h2>
    <ul class="toc">
__TOC__
    </ul>
  </div>
</section>

__BODY__

<section class="colophon">
  <p>隐 线 · 科 技 发 展 的 逻 辑</p>
  <p>正文约 __CHARS__ 千字　|　单行本　__DATE__</p>
  <p><a class="dl" href="__EPUB__" download>下载 EPUB 电子书</a> · 网页版可直接用浏览器打印为 PDF</p>
  <p>本书由 xquant-work / My-Books 书稿工程构建</p>
</section>

<div id="tools">
  <a id="epub" href="__EPUB__" download title="下载 EPUB 电子书">⬇</a>
  <button id="theme" title="切换明暗">◐</button>
  <button id="top" title="回到顶部">↑</button>
  <button id="print" title="打印 / 另存为 PDF">⎙</button>
</div>

<script>
(function(){
  var bar = document.getElementById('bar');
  function onScroll(){
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max * 100) : 0) + '%';
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();

  var root = document.documentElement;
  document.getElementById('theme').onclick = function(){
    root.dataset.theme = root.dataset.theme === 'night' ? 'paper' : 'night';
    try{ localStorage.setItem('ht-theme', root.dataset.theme); }catch(e){}
  };
  try{
    var saved = localStorage.getItem('ht-theme');
    if(saved) root.dataset.theme = saved;
  }catch(e){}

  document.getElementById('top').onclick = function(){
    window.scrollTo({top:0, behavior:'smooth'});
  };
  document.getElementById('print').onclick = function(){ window.print(); };
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
