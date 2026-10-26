"""把 foodmart.db 的 1998 年銷售資料轉成交易式 ARFF，加入子類別、商店類型、促銷（第 6-2 題）。

用法：python scripts/make_q6_sales_arff.py
輸出：arff/q6_sales_jan_nov.arff（sales_fact_1998，1～11 月）
      arff/q6_sales_dec.arff（sales_fact_dec_1998，12 月）

- 和第 5 題一樣，同一位顧客、同一天（customer_id + time_id）買的東西算一筆交易
- 同一天在兩家以上商店買東西的交易整筆排除，讓每筆交易只屬於一家店
- 每筆交易的 item：
  - 子類別：product_class 的 product_subcategory，每種一個 {t} 屬性
    （Coffee 同時屬於 Dry Goods 和 Hot Beverages 兩個 category，依名稱算同一個 item）
  - 商店類型：store_type 一個 nominal 屬性（5 種，不含沒有銷售的 HeadQuarters），每筆交易都有值
  - 促銷：promotion {t}，這一籃有任何一件促銷商品（promotion_id 不是 0 = No Promotion）就記 t
- 子類別、促銷沒有的記 ?；兩個檔案用同一組屬性，方便比較
"""
from collections import defaultdict
from pathlib import Path
import sqlite3

HW1 = Path(__file__).resolve().parent.parent
TABLES = [("sales_fact_1998", "q6_sales_jan_nov"), ("sales_fact_dec_1998", "q6_sales_dec")]
NO_PROMOTION = 0


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    con = sqlite3.connect(HW1 / "foodmart.db")
    subcats = sorted(r[0] for r in con.execute("SELECT DISTINCT product_subcategory FROM product_class"))
    # HeadQuarters 是總部，沒有銷售紀錄，不列為屬性
    stores = sorted(r[0] for r in con.execute(
        "SELECT DISTINCT store_type FROM store WHERE store_type != 'HeadQuarters'"))
    attrs = subcats + ["promotion"]
    index = {a: i for i, a in enumerate(attrs)}

    for table, name in TABLES:
        rows = con.execute(f"""
            SELECT s.customer_id, s.time_id, s.store_id, pc.product_subcategory, st.store_type, s.promotion_id
            FROM "{table}" s
            JOIN product p ON s.product_id = p.product_id
            JOIN product_class pc ON p.product_class_id = pc.product_class_id
            JOIN store st ON s.store_id = st.store_id
        """).fetchall()
        baskets = defaultdict(set)
        store_ids = defaultdict(set)
        store_type = {}
        for cust, day, store_id, subcat, store, promo in rows:
            items = baskets[(cust, day)]
            items.add(subcat)
            if promo != NO_PROMOTION:
                items.add("promotion")
            store_ids[(cust, day)].add(store_id)
            store_type[(cust, day)] = store
        multi_store = [key for key, ids in store_ids.items() if len(ids) > 1]
        for key in multi_store:
            del baskets[key]

        out = HW1 / "arff" / f"{name}.arff"
        out.parent.mkdir(exist_ok=True)
        with open(out, "w", encoding="ascii", newline="\n") as f:
            f.write(f"@relation {name}\n\n")
            for a in subcats:
                f.write(f"@attribute {quote(a)} {{t}}\n")
            f.write(f"@attribute store_type {{{','.join(quote(s) for s in stores)}}}\n")
            f.write("@attribute promotion {t}\n")
            f.write("\n@data\n")
            for key in sorted(baskets):
                row = ["?"] * len(attrs)
                for a in baskets[key]:
                    row[index[a]] = "t"
                row.insert(len(subcats), quote(store_type[key]))
                f.write(",".join(row) + "\n")

        n = len(baskets)
        sub_sizes = [len(b & set(subcats)) for b in baskets.values()]
        used = len({a for b in baskets.values() for a in b if a in set(subcats)})
        promo = sum(1 for b in baskets.values() if "promotion" in b)
        print(f"[{table}]")
        print(f"  交易數（顧客 + 日期）：{n}（已排除跨兩家以上商店的 {len(multi_store)} 筆）")
        print(f"  屬性數：{len(attrs) + 1}（子類別 {len(subcats)}，實際出現 {used} 種；store_type 1（{len(stores)} 種）；促銷 1）")
        print(f"  每筆交易的子類別數：平均 {sum(sub_sizes) / n:.2f}，最少 {min(sub_sizes)}，最多 {max(sub_sizes)}")
        print(f"  含促銷商品的交易：{promo}（{promo / n:.1%}）")
        print(f"  輸出：{out}（{out.stat().st_size / 1e3:.0f} KB）")
    con.close()


if __name__ == "__main__":
    main()
