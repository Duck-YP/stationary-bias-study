# Research roadmap

| ID | Research question | Method | Scope |
| --- | --- | --- | --- |
| P0 | 一維 stochastic SCAFFOLD stationary-bias 基線 | 獨立 chains、batch means 與預先指定 gates | 出版設定、程式與 artifacts 的可重現基線 |
| P1 | matched FedAvg vs SCAFFOLD 的 coefficient attribution | common random numbers、paired stopping 與 paired inference | 14-setting small-step matrix與 fixed-γ large-N matrix |
| P2 | multidimensional homogeneous SCAFFOLD validation | controlled vector recursion、exact targets、coordinate rotation、fixed-γ large-N extrapolation 與 coordinatewise inference | d=2 engineering smoke、d=2 coefficient/rotation/plateau matrices與 d=5 controlled validation |

本表只收錄 repository 內已有實作、設定或 artifact 的研究問題；精確矩陣、公式與數值
結果分別由各 workstream 的 config、程式及 manifest 定義。
