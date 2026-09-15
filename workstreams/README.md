# Workstream index

每個 workstream 代表一個可獨立說明、執行、驗證與保存 artifacts 的研究問題。
內部 ID 使用 `P<number>`，資料夾 slug 再補上可讀的題目名稱；目前索引為 P0 與 P1。

| ID | Slug | Research question | 主要入口 |
| --- | --- | --- | --- |
| P0 | `p0_scaffold_bias` | SCAFFOLD stationary-bias publication baseline | `python run.py p0 check` |
| P1 | `p1_matched_fedavg` | Matched FedAvg vs SCAFFOLD coefficient attribution | `python run.py p1 check` |


索引只列出已有程式、設定或 artifact 的題目。研究問題、方法與範圍見 `ROADMAP.md`。

## Naming contract

- ID：固定使用小寫 CLI key `p0`～；文件顯示可寫成 `P0`～。
- Slug：`pN_<descriptive_name>`，只描述研究問題，不放日期、作者或舊章節代號。
- Config：以問題或矩陣命名，例如 `matched_fedavg.yaml`。
- Formal artifacts：`artifacts/formal/<matrix-id>/`；matrix ID 寫入 manifest。
- Smoke artifacts：固定為 `artifacts/smoke/`，不可與 formal 共用路徑。
- Canonical formal output：乾淨 commit、staging 建置、raw scientific fields 一致後取代。
- Archive：只供保存與查閱，不是 formal runner 的輸出目標。
