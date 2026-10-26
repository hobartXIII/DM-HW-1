"""把 foodmart.db 的 1998 年 1～11 月銷售資料轉成交易式 ARFF，子類別分成原價和促銷兩種 item（第 6-2 題）。

用法：python scripts/make_q6_promo_arff.py
輸出：arff/q6_promo.arff（sales_fact_1998，1～11 月）

- 和第 5 題一樣，同一位顧客、同一天（customer_id + time_id）買的東西算一筆交易
- 每個子類別（product_class 的 product_subcategory）有兩個 {t} 屬性：
  - X：這一籃的 X 都是原價買的（promotion_id = 0，No Promotion）
  - P_X：這一籃的 X 至少有一件是促銷時買的
  同一籃的同一個子類別只會記在其中一個
- 沒有的記 ?
"""
from collections import defaultdict
from pathlib import Path
import sqlite3

HW1 = Path(__file__).resolve().parent.parent
NO_PROMOTION = 0


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    con = sqlite3.connect(HW1 / "foodmart.db")
    subcats = sorted(r[0] for r in con.execute("SELECT DISTINCT product_subcategory FROM product_class"))
    attrs = subcats + ["P_" + s for s in subcats]
    index = {a: i for i, a in enumerate(attrs)}

    rows = con.execute("""
        SELECT s.customer_id, s.time_id, pc.product_subcategory, s.promotion_id
        FROM sales_fact_1998 s
        JOIN product p ON s.product_id = p.product_id
        JOIN product_class pc ON p.product_class_id = pc.product_class_id
    """).fetchall()
    con.close()
    # (顧客, 日期) -> 子類別 -> 有沒有在促銷時買
    baskets = defaultdict(lambda: defaultdict(bool))
    for cust, day, subcat, promo in rows:
        baskets[(cust, day)][subcat] |= promo != NO_PROMOTION

    out = HW1 / "arff" / "q6_promo.arff"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="ascii", newline="\n") as f:
        f.write("@relation q6_promo\n\n")
        for a in attrs:
            f.write(f"@attribute {quote(a)} {{t}}\n")
        f.write("\n@data\n")
        for key in sorted(baskets):
            row = ["?"] * len(attrs)
            for subcat, promo in baskets[key].items():
                row[index[("P_" if promo else "") + subcat]] = "t"
            f.write(",".join(row) + "\n")

    n = len(baskets)
    sizes = [len(b) for b in baskets.values()]
    promo = sum(1 for b in baskets.values() if any(b.values()))
    used = len({("P_" if p else "") + s for b in baskets.values() for s, p in b.items()})
    print(f"交易數（顧客 + 日期）：{n}")
    print(f"屬性數：{len(attrs)}（子類別 {len(subcats)} × 原價／促銷，實際出現 {used} 種）")
    print(f"每筆交易的子類別數：平均 {sum(sizes) / n:.2f}，最少 {min(sizes)}，最多 {max(sizes)}")
    print(f"含促銷商品的交易：{promo}（{promo / n:.1%}）")
    print(f"輸出：{out}（{out.stat().st_size / 1e3:.0f} KB）")


if __name__ == "__main__":
    main()
