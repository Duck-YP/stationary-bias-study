# Stationary Bias Study

這個 repository 依研究 workstream 垂直切分。第一次進入專案時，只需要先看
`workstreams/README.md`，再進入 `P0` 或 `P1`；不用先理解舊論文章節代號。

數值模擬的定位是反證與診斷工具，不單獨構成數學證明。

## 快速入口

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe run.py list
.\.venv\Scripts\python.exe run.py check
.\.venv\Scripts\python.exe run.py test
```

所有操作都由根目錄的 `run.py` 進入，再明確指定 workstream：

```text
python run.py list
python run.py check
python run.py test

python run.py p0 check
python run.py p0 smoke
python run.py p0 run coefficient-convergence
python run.py p0 run client-count-scaling
python run.py p0 run negative-controls
python run.py p0 run small-step-confirmation
python run.py p0 report
python run.py p0 plot

python run.py p1 check
python run.py p1 smoke
python run.py p1 run
python run.py p1 report
python run.py p1 plateau check
python run.py p1 plateau smoke
python run.py p1 plateau run
python run.py p1 plateau report
```

`python run.py p1 run` 與 `python run.py p1 plateau run` 是正式 matched-pair
simulation；不是日常檢查指令。正式執行只接受乾淨且已有 commit 的來源，輸出採
受控覆寫。

## 專案地圖

```text
run.py                         唯一的專案級 CLI 入口
shared/configs/                跨 workstream 共用的數值預設
workstreams/
  README.md                    workstream 索引與命名規則
  ROADMAP.md                   現有研究問題、方法與邊界
  p0_scaffold_bias/            出版基線研究
    README.md                  P0 目的、入口與輸出說明
    study.yaml                 可機讀的識別與路徑
    configs/                   P0 專屬設定
    artifacts/                 P0 結果、圖與報告
  p1_matched_fedavg/           matched FedAvg vs SCAFFOLD
    README.md                  P1 目的、入口與輸出說明
    study.yaml                 可機讀的識別與路徑
    configs/                   P1 專屬設定
    artifacts/                 smoke 與 formal 輸出隔離
src/stationary_bias/
  cli.py                       workstream 路由
  core/                        共用模型、演算法、推論、I/O、理論
  workstreams/                 各 workstream 的模擬與分析實作
tests/
  core/                        共用核心測試
  workstreams/                 與實作同名的 workstream 測試
docs/                          跨 workstream 的方法與架構說明
```

## 分流原則

- 跨研究問題且語意穩定的程式放 `src/stationary_bias/core/`。
- 只服務單一研究問題的程式、設定、結果與說明放在同一個 workstream 名下。
- `smoke` 與 `formal` 輸出分開；P1 正式快照位於帶 matrix ID 的目錄。
- 只有已有程式、設定或 artifact 的 workstream 才出現在索引及 CLI。
- 現行程式與設定使用 workstream ID 及描述性名稱；舊章節縮寫不再是執行介面的一部分。

更多細節見 [workstream 索引](workstreams/README.md)與
[架構資料流](docs/project_structure.md)。

## 可重現性邊界

每條 chain 使用獨立 NumPy RNG，正式 seeds 與矩陣由設定檔固定。
`requirements.lock` 記錄參考套件版本。CSV 是主要數值紀錄；PNG 在不同作業系統間
不要求 byte-identical。

P1 正式執行先記錄來源 commit、dirty state、config hash、matrix ID、seeds 與套件
版本，再於 staging 目錄產生完整輸出。同一 matrix ID 已有結果時，三份原始 CSV
必須在排除 commit／dirty provenance 欄位後逐欄逐列相同，才會整體取代 canonical
目錄；不相同則保留原目錄並停止。`report` 可由原始 CSV 重建並覆寫衍生的摘要、
報告與圖片。出版 archive 不屬於受控覆寫目標。
