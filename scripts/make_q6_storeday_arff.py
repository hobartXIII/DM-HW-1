"""把 foodmart.db 的 1998 年銷售資料轉成「一家店一天」的 ARFF，看促銷和銷售量的關聯（第 6-2 題）。

用法：python scripts/make_q6_storeday_arff.py
輸出：arff/q6_storeday.arff（sales_fact_1998 + sales_fact_dec_1998，1998 全年）

- 同一家店、同一天（store_id + time_id）算一筆交易
- 每筆交易的屬性：
  - promotion：這一天有沒有促銷（yes／no）。同一家店同一天的銷售只會有一個 promotion_id
  - media_type：促銷活動的廣告媒體（promotion.media_type），沒有促銷的日子記 ?
  - day：星期幾（time_by_day.the_day）
  - month：月份（time_by_day.month_of_year）
  - store_type：商店類型（store.store_type）
  - sales_level：當天賣出的件數（unit_sales 加總），和這家店自己全年的店日比，
    依三分位切成 low／mid／high，排除大店、小店的規模差異
"""
from collections import defaultdict
from pathlib import Path
import sqlite3

HW1 = Path(__file__).resolve().parent.parent


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + str(name).replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    con = sqlite3.connect(HW1 / "foodmart.db")
    rows = con.execute("""
        SELECT s.store_id, s.time_id, st.store_type, t.the_day, t.month_of_year, pr.media_type,
               s.promotion_id != 0, SUM(s.unit_sales)
        FROM (SELECT * FROM sales_fact_1998 UNION ALL SELECT * FROM sales_fact_dec_1998) s
        JOIN store st ON s.store_id = st.store_id
        JOIN time_by_day t ON s.time_id = t.time_id
        JOIN promotion pr ON s.promotion_id = pr.promotion_id
        GROUP BY s.store_id, s.time_id
    """).fetchall()
    con.close()

    # 每家店的三分位切點
    units = defaultdict(list)
    for store, *_, total in rows:
        units[store].append(total)
    cuts = {}
    for store, u in units.items():
        u.sort()
        cuts[store] = (u[len(u) // 3], u[2 * len(u) // 3])

    def level(store, total):
        low, high = cuts[store]
        return "low" if total < low else ("high" if total >= high else "mid")

    data = []
    for store, _, store_type, day, month, media, promo, total in rows:
        data.append(["yes" if promo else "no", media if promo else None, day, month, store_type,
                     level(store, total)])
    names = ["promotion", "media_type", "day", "month", "store_type", "sales_level"]

    out = HW1 / "arff" / "q6_storeday.arff"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="ascii", newline="\n") as f:
        f.write("@relation q6_storeday\n\n")
        for i, name in enumerate(names):
            values = {d[i] for d in data if d[i] is not None}
            values = sorted(values) if name != "month" else sorted(values, key=int)
            f.write(f"@attribute {name} {{{','.join(quote(v) for v in values)}}}\n")
        f.write("\n@data\n")
        for d in data:
            f.write(",".join("?" if v is None else quote(v) for v in d) + "\n")

    n = len(data)
    promo = sum(1 for d in data if d[0] == "yes")
    print(f"交易數（店 + 日期）：{n}（{len(units)} 家店）")
    print(f"促銷日：{promo}（{promo / n:.1%}）")
    print("sales_level：" + "、".join(f"{lv} {sum(d[5] == lv for d in data)}" for lv in ("low", "mid", "high")))
    print(f"輸出：{out}（{out.stat().st_size / 1e3:.0f} KB）")


if __name__ == "__main__":
    main()
