# P0 — SCAFFOLD stationary-bias baseline

P0 保存一維 stochastic SCAFFOLD stationary-bias 出版研究，以及其小步長確認。
publication snapshot 是 baseline archive；不屬於 P1 受控覆寫目標。

## Entry points

```text
python run.py p0 check
python run.py p0 smoke
python run.py p0 run coefficient-convergence
python run.py p0 run client-count-scaling
python run.py p0 run negative-controls
python run.py p0 run small-step-confirmation
python run.py p0 report
python run.py p0 plot
```

## Contents

- `configs/`：P0 的四組研究矩陣與 gates。
- `artifacts/publication_snapshot/`：原始出版 CSV、PNG、report 與 manifest。
- `artifacts/small_step_confirmation/`：小步長確認的獨立輸出。
- `artifacts/smoke/`：可拋棄、被 Git 忽略的快速測試輸出。
- implementation：`src/stationary_bias/workstreams/p0_scaffold_bias/`。
- tests：`tests/workstreams/p0_scaffold_bias/`。
