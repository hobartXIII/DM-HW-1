"""找出 PDF 裡每個 [[Hn]] 標記在第幾頁，給 md2html.py 的目錄頁碼用。
用法：python findpages.py <in.pdf> <pages.json>

整份報告的轉檔流程（在 HW1/ 執行，out/ 自己指定一個暫存資料夾）：
1. python scripts/md2html.py report.md out/p1.html --markers
2. python scripts/print_pdf.py out/p1.html out/p1.pdf
3. python scripts/findpages.py out/p1.pdf out/pages.json
4. python scripts/md2html.py report.md out/final.html --toc-pages out/pages.json
5. python scripts/print_pdf.py out/final.html 5115056022.pdf
第 1 步的目錄頁碼先填 00，和第 4 步填入真的頁碼時寬度相同，所以版面不會跑掉
"""
import json
import re
import sys

from pypdf import PdfReader

r = PdfReader(sys.argv[1])
pages = {}
for i, p in enumerate(r.pages, 1):
    for m in re.findall(r"\[\[(h\d+)\]\]", p.extract_text().replace(" ", "")):
        pages.setdefault(m, i)
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(pages, f)
print(len(r.pages), "pages,", len(pages), "markers")
