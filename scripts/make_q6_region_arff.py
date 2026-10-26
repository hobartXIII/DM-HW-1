"""把 recipe.db 同一區域的幾個國家合成一份交易式 ARFF，最後加上 cuisine 屬性（第 6-3 題）。

用法：python scripts/make_q6_region_arff.py
輸出：
- arff/q6_east_asia.arff（Chinese + Japanese）
- arff/q6_europe.arff（German + Spanish）

- 一個 (國家, recipe_name) 算一筆交易；同一國家裡名稱相同的列合併，不同國家的同名食譜分開
- 每種食材一個屬性 {t}，照字母排序；有用到記 t，沒用到記 ?
- 最後一個屬性 cuisine 是 nominal，值為國家名稱，每筆交易都有值
- 不放 recipe_name 欄
"""
import sqlite3
from collections import defaultdict
from pathlib import Path

HW1 = Path(__file__).resolve().parent.parent
REGIONS = {
    "q6_east_asia": ["Chinese", "Japanese"],
    "q6_europe": ["German", "Spanish"],
}


def quote(name):
    # ARFF 名稱用單引號包起來，內部的 \ 和 ' 要跳脫
    return "'" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"


def make(con, relation, tables):
    # (國家, 食譜名稱) -> 食材
    baskets = defaultdict(set)
    for table in tables:
        for recipe, ingredient in con.execute(f'SELECT DISTINCT recipe_name, ingredient FROM "{table}"'):
            baskets[(table, recipe)].add(ingredient)
    items = sorted({ing for b in baskets.values() for ing in b})
    index = {ing: i for i, ing in enumerate(items)}

    out = HW1 / "arff" / f"{relation}.arff"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"@relation {relation}\n\n")
        for ing in items:
            f.write(f"@attribute {quote(ing)} {{t}}\n")
        f.write(f"@attribute cuisine {{{','.join(tables)}}}\n")
        f.write("\n@data\n")
        for key in sorted(baskets):
            row = ["?"] * len(items)
            for ing in baskets[key]:
                row[index[ing]] = "t"
            f.write(",".join(row + [key[0]]) + "\n")

    n = len(baskets)
    sizes = [len(b) for b in baskets.values()]
    counts = "、".join(f"{t} {sum(1 for k in baskets if k[0] == t)}" for t in tables)
    print(f"區域：{relation}（{' + '.join(tables)}）")
    print(f"交易數（國家 + 食譜名稱）：{n}（{counts}）")
    print(f"食材屬性數：{len(items)}（另加 cuisine 1 個），非 ASCII 名稱：{sum(1 for i in items if not i.isascii())}")
    print(f"每筆交易的食材數：平均 {sum(sizes) / n:.2f}，最少 {min(sizes)}，最多 {max(sizes)}")
    print(f"輸出：{out}（{out.stat().st_size / 1e6:.1f} MB）")


def main():
    con = sqlite3.connect(HW1 / "recipe.db")
    for relation, tables in REGIONS.items():
        make(con, relation, tables)
        print()
    con.close()


if __name__ == "__main__":
    main()
