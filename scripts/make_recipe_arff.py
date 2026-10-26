"""把 recipe.db 某個國家的資料表轉成交易式 ARFF。

用法：python scripts/make_recipe_arff.py Italian
輸出：arff/<table 小寫>.arff

- 一個 recipe_name 算一筆交易，名稱相同的列合併（同名的不同食譜不拆開，見報告 0.3）
- 每種食材一個屬性 {t}，照字母排序；有用到記 t，沒用到記 ?
- 一般非稀疏格式，不放 recipe_name 欄
"""
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HW1 = Path(__file__).resolve().parent.parent


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main(table):
    con = sqlite3.connect(HW1 / "recipe.db")
    rows = con.execute(f'SELECT DISTINCT recipe_name, ingredient FROM "{table}"').fetchall()
    con.close()

    baskets = defaultdict(set)
    for recipe, ingredient in rows:
        baskets[recipe].add(ingredient)
    items = sorted({ing for _, ing in rows})
    index = {ing: i for i, ing in enumerate(items)}

    out = HW1 / "arff" / f"{table.lower()}.arff"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="ascii", newline="\n") as f:
        f.write(f"@relation {table.lower()}\n\n")
        for ing in items:
            f.write(f"@attribute {quote(ing)} {{t}}\n")
        f.write("\n@data\n")
        for recipe in sorted(baskets):
            row = ["?"] * len(items)
            for ing in baskets[recipe]:
                row[index[ing]] = "t"
            f.write(",".join(row) + "\n")

    sizes = [len(b) for b in baskets.values()]
    print(f"資料表：{table}")
    print(f"去重後的 (食譜, 食材) 列數：{len(rows)}")
    print(f"交易數（食譜名稱）：{len(baskets)}")
    print(f"屬性數（食材種類）：{len(items)}")
    print(f"每筆交易的食材數：平均 {sum(sizes) / len(sizes):.2f}，最少 {min(sizes)}，最多 {max(sizes)}")
    print(f"輸出：{out}（{out.stat().st_size / 1e6:.1f} MB）")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Italian")
