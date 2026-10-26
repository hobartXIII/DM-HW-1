"""監測 Weka（javaw.exe）執行時的 CPU 與記憶體，並在固定時間點自動截全螢幕。

用法：python scripts/monitor_weka.py q1-1
  1. 先開好 Weka，載入資料、設好參數。
  2. 執行本腳本，等提示出現。
  3. 在 Weka 按 Start 的同時，在這裡按 Enter 開始計時。
  4. Weka 出錯或跑完就按 Ctrl+C 結束；到 30 分鐘會發出提示音，提醒你到 Weka 按 Stop，
     按完 Stop 後再按 Ctrl+C。Weka 視窗被關掉時，腳本也會自動結束。

輸出：
  logs/<label>_usage.csv          每 2 秒一筆
  screenshots/<label>_NN_Xmin.png 第 1、5、15、25 分鐘的全螢幕截圖

本腳本只觀察，不會操作 Weka。
"""
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil
from PIL import ImageGrab

HW1 = Path(__file__).resolve().parent.parent
INTERVAL = 2                     # 取樣間隔（秒）
SHOTS = [(60, "05_1min"), (300, "06_5min"), (900, "07_15min"), (1500, "08_25min")]
LIMIT = 30 * 60                  # 時間上限（秒）
MB = 1024 * 1024


def find_weka():
    """找執行 Weka 的 Java 行程；有好幾個時取記憶體最大的。"""
    found = []
    for p in psutil.process_iter(["name", "cmdline", "memory_info"]):
        try:
            if p.info["name"] and p.info["name"].lower() in ("javaw.exe", "java.exe"):
                cmd = " ".join(p.info["cmdline"] or []).lower()
                if "weka" in cmd:
                    found.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return max(found, key=lambda p: p.info["memory_info"].rss) if found else None


def main(label):
    proc = find_weka()
    while proc is None:
        input("找不到 Weka 的 Java 行程。請先開啟 Weka，再按 Enter 重試…")
        proc = find_weka()
    print(f"監測對象：{proc.info['name']}（PID {proc.pid}）")

    log_dir = HW1 / "logs"
    shot_dir = HW1 / "screenshots"
    log_dir.mkdir(exist_ok=True)
    shot_dir.mkdir(exist_ok=True)
    csv_path = log_dir / f"{label}_usage.csv"

    # 防止覆蓋之前的紀錄：同一個標籤的 CSV 或截圖已經存在就停止
    existing = [p for p in [csv_path] + [shot_dir / f"{label}_{n}.png" for _, n in SHOTS] if p.exists()]
    if existing:
        sys.exit("以下檔案已經存在，為避免覆蓋，已停止執行：\n  "
                 + "\n  ".join(str(p) for p in existing)
                 + "\n請改用其他標籤，或先自行確認並處理這些檔案。")

    ncpu = psutil.cpu_count()
    proc.cpu_percent(None)       # 第一次呼叫只是歸零
    input(f"\n[{label}] 在 Weka 按 Start 的同時，在這裡按 Enter 開始計時…")
    t0 = time.monotonic()
    print(f"開始：{datetime.now():%Y-%m-%d %H:%M:%S}，每 {INTERVAL} 秒記錄一次，Ctrl+C 結束\n")
    print(" 經過時間   CPU%(單核=100)  CPU%(全機)  記憶體RSS(MB)  Private(MB)")

    pending = list(SHOTS)
    warned = False
    end_reason = "使用者按 Ctrl+C"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "elapsed_s", "cpu_percent", "cpu_percent_total",
                    "rss_mb", "private_mb", "system_mem_percent"])
        try:
            while True:
                time.sleep(INTERVAL)
                elapsed = time.monotonic() - t0
                try:
                    cpu = proc.cpu_percent(None)
                    mem = proc.memory_info()
                except psutil.NoSuchProcess:
                    end_reason = "Weka 行程已結束"
                    break
                private = getattr(mem, "private", 0) / MB
                row = [f"{datetime.now():%H:%M:%S}", round(elapsed, 1), round(cpu, 1),
                       round(cpu / ncpu, 1), round(mem.rss / MB, 1), round(private, 1),
                       psutil.virtual_memory().percent]
                w.writerow(row)
                f.flush()
                m, s = divmod(int(elapsed), 60)
                print(f"\r  {m:02d}:{s:02d}     {row[2]:>8}       {row[3]:>7}     "
                      f"{row[4]:>10}   {row[5]:>10}", end="", flush=True)

                while pending and elapsed >= pending[0][0]:
                    _, name = pending.pop(0)
                    path = shot_dir / f"{label}_{name}.png"
                    ImageGrab.grab(all_screens=True).save(path)
                    print(f"\n  已截圖：{path.name}")

                if not warned and elapsed >= LIMIT:
                    warned = True
                    print("\n\n  *** 已滿 30 分鐘：請先手動截圖（結束時 B），再到 Weka 按 Stop，最後按 Ctrl+C ***\n")
                    try:
                        import winsound
                        for _ in range(3):
                            winsound.Beep(1000, 400)
                    except Exception:
                        print("\a", end="")
        except KeyboardInterrupt:
            pass

    elapsed = time.monotonic() - t0
    m, s = divmod(int(elapsed), 60)
    print(f"\n\n結束：{datetime.now():%Y-%m-%d %H:%M:%S}（{end_reason}），共 {m} 分 {s} 秒")
    print(f"紀錄：{csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法：python scripts/monitor_weka.py <標籤，例如 q1-1>")
    main(sys.argv[1])
