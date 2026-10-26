"""report.md -> 列印用 HTML（給 Chrome headless 轉 PDF），版面仿 Word 文件。
用法：python md2html.py <report.md> <out.html> [--markers] [--toc-pages pages.json]
- --markers：在每個標題後面加隱藏的 [[Hn]] 標記，轉成 PDF 後用來找標題在第幾頁
- --toc-pages：{ "h1": 2, ... }，目錄的頁碼；沒給就填 00（版面寬度相同）
"""
import html as htmllib
import json
import re
import sys
from pathlib import Path
from markdown_it import MarkdownIt

args = sys.argv[1:]
markers = "--markers" in args
pages = {}
if "--toc-pages" in args:
    pages = json.loads(Path(args[args.index("--toc-pages") + 1]).read_text(encoding="utf-8"))
src, out = Path(args[0]), Path(args[1])

# CommonMark + GFM 表格；breaks=True 讓原文的換行（一句一行）在 PDF 裡也換行
md = MarkdownIt("commonmark", {"breaks": True}).enable("table")
tokens = md.parse(src.read_text(encoding="utf-8"))
heads = []  # (id, level, text)
for i, tok in enumerate(tokens):
    if tok.type == "heading_open" and tok.tag in ("h2", "h3", "h4"):
        hid = f"h{len(heads) + 1}"
        tok.attrSet("id", hid)
        heads.append((hid, int(tok.tag[1]), tokens[i + 1].content.replace("**", "")))
body = md.renderer.render(tokens, md.options, {})

if markers:
    # 1pt 白字，不影響換行，只給 pypdf 找頁碼用
    body = re.sub(r'(<h[234] id="(h\d+)">.*?)(</h[234]>)',
                  lambda m: f'{m.group(1)}<span class="mk">[[{m.group(2)}]]</span>{m.group(3)}', body)

toc = ['<div class="toc"><div class="toc-title">目錄</div>']
for hid, level, text in heads:
    toc.append(f'<div class="toc-row l{level}"><span class="t">{htmllib.escape(text)}</span>'
               f'<span class="d"></span><span class="p">{pages.get(hid, "00")}</span></div>')
toc.append("</div>")
# 目錄放在標題資訊之後、第一個大題之前
body = body.replace("<h2", "\n".join(toc) + "<h2", 1)

base = src.parent.resolve().as_uri() + "/"
css = """
/* Word 預設：A4、上下左右 2.54 cm 邊界 */
@page { size: A4; margin: 25.4mm; }
body { font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif; font-size: 11pt; line-height: 1.5; color: #000; }
p { margin: 0 0 8pt; }
/* 標題仿 Word 內建的標題 1～4 樣式；大題不強制換頁，只避免標題留在頁尾 */
h1 { font-size: 20pt; font-weight: bold; color: #1F3864; margin: 0 0 10pt; }
h2 { font-size: 16pt; font-weight: bold; color: #2F5496; margin: 22pt 0 8pt; }
h3 { font-size: 13pt; font-weight: bold; color: #2F5496; margin: 14pt 0 6pt; }
h4 { font-size: 12pt; font-weight: bold; color: #1F3864; margin: 12pt 0 6pt; }
h2, h3, h4 { break-after: avoid; }
.mk { font-size: 1pt; color: #fff; }
/* 目錄：一頁，點線連到頁碼 */
.toc { break-after: page; margin-top: 14pt; }
.toc-title { font-size: 16pt; font-weight: bold; color: #2F5496; margin-bottom: 8pt; }
.toc-row { display: flex; align-items: baseline; font-size: 10.5pt; line-height: 1.6; }
.toc-row.l2 { font-weight: bold; margin-top: 4pt; }
.toc-row.l3 { padding-left: 16pt; }
.toc-row.l4 { padding-left: 32pt; }
.toc-row .d { flex: 1; border-bottom: 1pt dotted #808080; margin: 0 4pt; }
ul, ol { margin: 0 0 8pt; padding-left: 22pt; }
li { margin: 0 0 3pt; }
/* 表格仿 Word「表格格線」：細黑框線 */
table { border-collapse: collapse; width: 100%; margin: 4pt 0 10pt; font-size: 10pt; line-height: 1.35; break-inside: auto; }
th, td { border: 0.5pt solid #000; padding: 3pt 6pt; vertical-align: top; }
th { background: #D9E2F3; font-weight: bold; }
tr { break-inside: avoid; }
/* 程式碼只在空白處換行，不把字切開 */
pre { background: #F2F2F2; border: 0.5pt solid #BFBFBF; padding: 6pt; font-size: 8pt; line-height: 1.35;
      white-space: pre-wrap; word-break: normal; overflow-wrap: normal; margin: 4pt 0 10pt; }
code { font-family: Consolas, "Microsoft JhengHei", monospace; }
/* 行內程式碼和周圍文字同大小 */
p code, li code, td code, th code { font-size: 1em; }
img { max-width: 100%; max-height: 120mm; display: block; margin: 6pt auto 4pt; break-inside: avoid; }
/* 圖片和下一行的圖說在同一段，置中 */
p:has(> img) { text-align: center; font-size: 10pt; color: #404040; break-inside: avoid; }
blockquote { border-left: 3pt solid #2F5496; margin: 6pt 0 10pt; padding: 2pt 10pt; color: #404040; }
hr { display: none; }
"""
html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<base href="{base}"><title>{src.stem}</title><style>{css}</style></head><body>{body}</body></html>"""
out.write_text(html, encoding="utf-8")
print("ok", out, len(heads), "headings")
