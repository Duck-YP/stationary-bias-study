# P1 — Matched FedAvg vs SCAFFOLD

P1 使用 common random numbers 比較 homogeneous FedAvg 與 SCAFFOLD，將 stationary-bias
coefficient 的差異做 pair-level 歸因。兩個 kernel 共用同一 fresh-noise block、batch
boundary 與停止決策，Delta 使用 paired chain differences 推論。

## Entry points

```text
python run.py p1 check     # 只驗證 14 settings / 112 matched pairs
python run.py p1 smoke     # 小型、非科學結論的端到端檢查
python run.py p1 run       # 由乾淨 commit 執行正式 simulation，採受控覆寫
python run.py p1 report    # 從 canonical raw CSV 重建衍生輸出；無 canonical 時顯示 archive
```

## Contents

- `configs/matched_fedavg.yaml`：P1 矩陣、seeds、stopping 與 gates。
- `artifacts/smoke/`：可拋棄且被 Git 忽略的 smoke 輸出。
- `artifacts/formal/<matrix-id>/`：正式 CSV、manifest、報告與 PNG 快照。
- `artifacts/archive/original_formal_snapshot/`：改名前保存的出版快照，不是覆寫目標。
- implementation：`src/stationary_bias/workstreams/p1_matched_fedavg/`。
- tests：`tests/workstreams/p1_matched_fedavg/`。

## Fixed-γ large-N plateau

這個獨立 formal matrix 固定 `H=2`、`γ=1/24`，只改變
`N ∈ {8, 16, 32, 64, 128}`，每個 setting 使用 8 個 matched chain pairs
（共 40 pairs）。目的在檢查 FedAvg、SCAFFOLD 與 pair-level difference 的
normalized coefficient 是否在 `1/N → 0` 時形成與理論 sign/order 相容的平台。

```text
python run.py p1 plateau check
python run.py p1 plateau smoke
python run.py p1 plateau run
python run.py p1 plateau report
```

- stable matrix ID：`p1-fixed-gamma-large-n-h2-gamma-1over24`
- config：`configs/fixed_gamma_large_n.yaml`
- formal artifacts：`artifacts/formal/p1-fixed-gamma-large-n-h2-gamma-1over24/`
- theory targets：FedAvg `-0.125`、SCAFFOLD `-0.1875`、paired delta `-0.0625`
- inference：primary estimator 是 stationary mean-balance；delta 與 `1/N` extrapolation
  使用 matched-pair uncertainty。

## Controlled overwrite

兩個 formal runner 都在任何輸出寫入前擷取 commit、source dirty state、config hashes、
environment、matrix ID 與 seeds，並要求來源乾淨。所有 raw 與 derived artifacts 先寫入
staging 目錄。若 canonical 目錄已存在，`run_summary.csv`、`pair_summary.csv` 與
`batch_summary.csv` 排除 commit／dirty provenance 欄位後，identifier、設定、gates 與
離散欄位必須完全相同；明確列出的連續數值欄位只容許跨平台浮點 roundoff
（relative `5e-11`、absolute `2e-12`；除以 gamma squared 的 direct-mean 診斷欄位
`C_direct` 使用 absolute `2e-11`）。通過後才會以 staging 目錄整體取代，否則保留原結果
並停止。Archive 不會被讀作覆寫目標。
