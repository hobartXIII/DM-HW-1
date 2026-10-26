"""把 foodmart.db 的 customer 表中第 4 題指定的 9 個屬性轉成 ARFF。

用法：python scripts/make_customer_arff.py
輸出：arff/customer.arff

- 一位顧客一筆資料
- 文字欄位寫成 nominal 屬性，值依字母排序
- 整數欄位（total_children、num_children_at_home、num_cars_owned）保留為 numeric，
  在 Weka 的 Preprocess 用 NumericToNominal 濾鏡轉成類別
"""
import sqlite3
from pathlib import Path

HW1 = Path(__file__).resolve().parent.parent
COLUMNS = ["state_province", "yearly_income", "gender", "total_children",
           "num_children_at_home", "education", "occupation", "houseowner", "num_cars_owned"]
NUMERIC = {"total_children", "num_children_at_home", "num_cars_owned"}


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + str(name).replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    con = sqlite3.connect(HW1 / "foodmart.db")
    cols = ", ".join(f'"{c}"' for c in COLUMNS)
    rows = con.execute(f"SELECT {cols} FROM customer ORDER BY customer_id").fetchall()
    con.close()

    out = HW1 / "arff" / "customer.arff"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="ascii", newline="\n") as f:
        f.write("@relation customer\n\n")
        for j, col in enumerate(COLUMNS):
            if col in NUMERIC:
                f.write(f"@attribute {col} numeric\n")
            else:
                values = sorted({r[j] for r in rows})
                f.write(f"@attribute {col} {{{','.join(quote(v) for v in values)}}}\n")
        f.write("\n@data\n")
        for r in rows:
            f.write(",".join(str(v) if COLUMNS[j] in NUMERIC else quote(v)
                             for j, v in enumerate(r)) + "\n")

    print(f"資料筆數（顧客）：{len(rows)}")
    print(f"屬性數：{len(COLUMNS)}（numeric：{', '.join(c for c in COLUMNS if c in NUMERIC)}）")
    print(f"輸出：{out}（{out.stat().st_size / 1e3:.0f} KB）")


if __name__ == "__main__":
    main()
