"""把 foodmart.db 的 1998 年銷售資料轉成交易式 ARFF（第 5 題）。

用法：python scripts/make_sales_arff.py
輸出：arff/sales_1998_jan_nov.arff（sales_fact_1998，1～11 月）
      arff/sales_1998_dec.arff（sales_fact_dec_1998，12 月）

- 同一位顧客、同一天（customer_id + time_id）買的東西算一筆交易
- 商品歸到 product_class 的 product_category（47 種），每個 category 一個 {t} 屬性；
  有買記 t，沒買記 ?，同一籃買了同一類的多件商品只記一次
- 兩個檔案用同一組屬性（全部 47 種 category，照字母排序），方便比較
"""
from collections import defaultdict
from pathlib import Path
import sqlite3

HW1 = Path(__file__).resolve().parent.parent
TABLES = [("sales_fact_1998", "sales_1998_jan_nov"), ("sales_fact_dec_1998", "sales_1998_dec")]


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    con = sqlite3.connect(HW1 / "foodmart.db")
    categories = sorted(r[0] for r in con.execute("SELECT DISTINCT product_category FROM product_class"))
    index = {c: i for i, c in enumerate(categories)}

    for table, name in TABLES:
        rows = con.execute(f"""
            SELECT DISTINCT s.customer_id, s.time_id, pc.product_category
            FROM "{table}" s
            JOIN product p ON s.product_id = p.product_id
            JOIN product_class pc ON p.product_class_id = pc.product_class_id
        """).fetchall()
        baskets = defaultdict(set)
        for cust, day, cat in rows:
            baskets[(cust, day)].add(cat)

        out = HW1 / "arff" / f"{name}.arff"
        out.parent.mkdir(exist_ok=True)
        with open(out, "w", encoding="ascii", newline="\n") as f:
            f.write(f"@relation {name}\n\n")
            for c in categories:
                f.write(f"@attribute {quote(c)} {{t}}\n")
            f.write("\n@data\n")
            for key in sorted(baskets):
                row = ["?"] * len(categories)
                for c in baskets[key]:
                    row[index[c]] = "t"
                f.write(",".join(row) + "\n")

        sizes = [len(b) for b in baskets.values()]
        used = len({c for b in baskets.values() for c in b})
        print(f"[{table}]")
        print(f"  交易數（顧客 + 日期）：{len(baskets)}")
        print(f"  屬性數（category）：{len(categories)}，實際出現 {used} 種")
        print(f"  每筆交易的 category 數：平均 {sum(sizes) / len(sizes):.2f}，最少 {min(sizes)}，最多 {max(sizes)}")
        print(f"  輸出：{out}（{out.stat().st_size / 1e3:.0f} KB）")
    con.close()


if __name__ == "__main__":
    main()
