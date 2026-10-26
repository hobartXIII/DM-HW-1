# HW1 附錄

報告本文在 `report.md`，輸出成 `5115056022.pdf`；這份附錄不放進 PDF

## A. 資料轉換與監測腳本

都放在 `scripts/`，用 Python 3.11 的 `sqlite3` 讀取資料庫

| 腳本 | 用於 | 輸入 | 輸出 |
|---|---|---|---|
| `make_recipe_arff.py <國家>` | 第 1、2、3 題 | recipe.db 的 Italian、Thai 表 | `italian.arff`、`thai.arff` |
| `make_customer_arff.py` | 第 4 題、6-1 | foodmart.db 的 customer 表 | `customer.arff` |
| `make_sales_arff.py` | 第 5 題 | sales_fact_1998、sales_fact_dec_1998、product、product_class | `sales_1998_jan_nov.arff`、`sales_1998_dec.arff` |
| `make_q6_storeday_arff.py` | 6-2 | sales_fact_1998、sales_fact_dec_1998、store、time_by_day、promotion | `q6_storeday.arff` |
| `make_q6_region_arff.py` | 6-3 | recipe.db 的 Chinese、Japanese、German、Spanish 表 | `q6_east_asia.arff`、`q6_europe.arff` |
| `monitor_weka.py <標籤>` | 第 1 題 | — | 監測 Weka 的 CPU 與記憶體，並定時截圖 |

## B. 產生的 ARFF 檔案

都放在 `arff/`

| 檔案 | 用於 | 筆數 | 屬性數 |
|---|---|---|---|
| `italian.arff` | 第 1、2、3 題 | 6,560 | 2,398 |
| `thai.arff` | 第 3 題 | 952 | 879 |
| `customer.arff` | 第 4 題、6-1 | 10,281 | 9 |
| `sales_1998_jan_nov.arff` | 第 5 題 | 34,015 | 47 |
| `sales_1998_dec.arff` | 第 5 題 | 3,771 | 47 |
| `q6_storeday.arff` | 6-2 | 1,440 | 6 |
| `q6_east_asia.arff` | 6-3 | 2,483 | 1,408 |
| `q6_europe.arff` | 6-3 | 2,105 | 1,732 |

## C. 第 1 題的執行時間與資源使用

執行時間取自 Weka Log 的起訖時間；CPU 和記憶體用 `scripts/monitor_weka.py` 監測 Java 行程

| 項目 | Apriori（1-1） | FPGrowth（1-2） |
|---|---|---|
| Weka Log | 18:11:44 開始、18:20:20 結束，516 秒 | 18:38:30 開始、18:38:31 結束，約 1 秒（Log 只記到秒） |
| CPU | 執行期間一直約 100%（以單一核心為 100%），等於用滿 1 個核心，約占全機 16 個執行緒的 6% | 執行時間太短，監測沒有記錄到執行過程 |
| 記憶體 | Java 行程的 RSS 從約 803 MB 增加到約 1,677 MB，Private 從約 1,094 MB 增加到約 2,500 MB，大約在結束前 1 分鐘開始明顯上升；Weka 的 Memory usage 視窗顯示 heap 用量一直遠低於約 8 GB 的上限 | 同上 |

- **限制**：Apriori 的資源監測比 Weka 開始執行晚了約 5 分 47 秒，所以 CPU 和記憶體只記錄到後段；執行時間以 Weka Log 為準
