"""用 Chrome DevTools Protocol 把 HTML 印成 PDF，頁尾加頁碼。
用法：python print_pdf.py <in.html> <out.pdf>
"""
import asyncio
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9333
FOOTER = ('<div style="width:100%;text-align:center;font-size:9pt;'
          'font-family:\'Microsoft JhengHei\',sans-serif;color:#404040">'
          '<span class="pageNumber"></span> / <span class="totalPages"></span></div>')


async def run(ws_url, url, out):
    async with websockets.connect(ws_url, max_size=None) as ws:
        n = 0

        async def call(method, **params):
            nonlocal n
            n += 1
            await ws.send(json.dumps({"id": n, "method": method, "params": params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == n:
                    if "error" in msg:
                        raise RuntimeError(msg["error"])
                    return msg["result"]

        await call("Page.enable")
        await call("Page.navigate", url=url)
        await call("Runtime.evaluate", awaitPromise=True,
                   expression="new Promise(r => { const go = () => document.fonts.ready.then(() => r(1));"
                              " document.readyState === 'complete' ? go() : addEventListener('load', go); })")
        res = await call("Page.printToPDF", preferCSSPageSize=True, printBackground=True,
                         displayHeaderFooter=True, headerTemplate="<span></span>", footerTemplate=FOOTER)
        Path(out).write_bytes(base64.b64decode(res["data"]))


def main():
    src, out = Path(sys.argv[1]).resolve(), sys.argv[2]
    prof = tempfile.mkdtemp(prefix="chrome-pdf-")
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
                             f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
                page = next(t for t in targets if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError("Chrome 沒有啟動")
        asyncio.run(run(page["webSocketDebuggerUrl"], src.as_uri(), out))
        print("ok", out)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
