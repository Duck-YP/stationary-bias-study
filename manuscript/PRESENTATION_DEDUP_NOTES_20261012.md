# SCAFFOLD：主文實驗整合、Significance 精煉與 Appendix C 去重

## 版本

- 基底：`SCAFFOLD_Full_Updated_20261010.zip`，38 頁。
- 本輪整合：2026-10-12；36 頁（主文 17、References 2、附錄 17）。
- 編譯入口：`manuscript/main.tex`；在該目錄執行 `sh build.sh`。
- 僅四個正文／附錄檔案改動：Introduction、Numerical Study、Discussion、Appendix C。

## Introduction / Discussion

Contribution list 改為簡潔的成果索引；Significance and scope 集中說明既有展開
未解析的二階差異、controls 的額外貢獻與 H-dependence，以及更一般設定的解析參考。
Introduction 現在結束於第 2 頁。Discussion 以正面方式定位 characterization，
並只用一段統一說明 real-data 的 finite-tail / post-hoc interpretation 角色，
不重複列出未建立 prediction improvement 的辯護。

## 主文實驗

1. **Table 2** 不再只有三列 matched difference；改為九列向量摘要，涵蓋
   SCAFFOLD、FedAvg 與 separately simulated paired difference 的 H=2 primary、
   H=4 primary、H=4 smaller-step。目標與估計向量一一並列，
   **主文統一顯示七位小數**，不是重新估計。
2. **Table 5** 由原 Appendix C.12 移到 Section 6.5，保留全部六個 nonzero-proxy
   E5 配置。欄名改為 Cosine / Projection ratio / Relative residual；
   caption 直接定義三個量，沒有將 projection ratio 誤稱為 norm ratio 或 MSE 解釋比例。
3. Section 6.3 補上簡短的 disjoint IID / label-skew contextual interpretation，
   指向 C.9，不在主文重列整張 heterogeneous-performance 表。
4. E4 的兩個獨立圖形 panels 不重繪、不縮放；調整局部 float placement，
   使 E4 圖及 E5 表跟隨各自小節，不漂到 Conclusion 之後。

## Appendix C 的去重方式

| 小節 | 主文保留 | 附錄保留 / 移除的重複 |
|---|---|---|
| C.1–C.2 | 主要 grid、實驗規模與 normalization | estimator、smaller-step grid、burn-in / batching / inference；移動 primary-grid equation 至 6.1，保留原 label |
| C.3 | Table 2 的九列 target / estimate vectors | Table 6 只列十八個座標的原始 simultaneous intervals，不重列 estimates 或 targets |
| C.4 | Historical H=4 結果與必要界線 | 保留 residual table / figure、post-hoc fit、不可分辨的誤差來源；刪除重複總結 |
| C.5 | fixed-step curves 與 d=5 結果摘要 | fixed-step CI / offsets；完整 d=5 表；不重列圖上 fitted points 與共同 target |
| C.6–C.8 | 主要 control fits、affine residual 與 H=8 摘要 | 保留 secondary-estimator discrepancies、rotation identities、leading-intercept 表與獨立 study protocol；刪除重複主結論 |
| C.9 | Figure 3 的 R0 projections | R0 只補充 raw-checkpoint MSE / test loss；R1/R2 保留完整數值與區間，不重列 R0 projection paths |
| C.10 | 不另擴写 | 保留 batch reconstruction、H=1 numerical flags 及未完成的核查範圍 |
| C.11 | Figure 4、主要 shares / contrasts 與 averaging budget | estimator、額外 absolute statistics / loss intervals、cross term、完整 temporal / crossover 診斷；不重列已呈現的 U/V/shares/paired-MSE summary |
| C.12 | Table 5 的全部 E5 K=64 point summaries 與解釋 | 只保留 reference directions、log slopes、短窗口、H-ratio uncertainty 及 resampling；不再重列六組主表或逐組 point-summary 敘述 |

去重刪的是呈現上的重複，不是原始結果。必要的設定、區間和結果解釋仍然就近可查。
C.11 尚保留的 absolute MSE / objective values 和額外 intervals 是主文圖文沒有完整呈現的內容。

## 原始數值與不理想結果

- 129 個既有 supplementary-results 檔案、32 個 figure-related 檔案全部逐檔 hash 相同。
- 主文係數摘要的原精度資料另存為
  `supplementary_results/presentation_source/historical_coefficient_intercepts.csv`。
- 舊版相關表格的原始 cells 保存在同目錄的 `original_table_cells.json`，
  僅供追溯，不是 active LaTeX input。
- Historical H=4 primary / smaller-step target exclusions、H=8 gaps、
  四筆 direct–balance discrepancies、H=1 long-horizon flags、E4 的 144 個
  temporal-equivalence gates、E5 H=4/H=2 ratio 與各 uncertainty intervals 均保留。
- 沒有把 E4 的 finite-tail interpretation 改成 stationary floor 認證，
  也沒有將 E5 的 directional agreement 改成 exact control-prefactor validation。

## 驗證

- 309 項本輪 source / numerical-relocation / layout checks：0 項失敗。
- 再執行既有 E4/E5 保存值一致性檢查：1,507 組、221,919 個 scalar comparisons，
  0 項失敗；本輪沒有從 batch arrays 重建，不表示又進行了一次完整 batch audit。
- 九個 active figure panels 的最小最終文字約 9.66 PDF pt；
  原圖、尺寸、字型設定均未修改。
- 定理、命題、證明 A/B、Setting、Main Results、Mechanism、Related Work、
  Conclusion、bibliography、macros、main.tex 均與基底位元組相同。
- 公式 / 表格編號因移動而自動更新；原有 labels 均保留，沒有重複 active labels。
- 本輪沒有新訓練、新擬合、bootstrap 或 proof audit。

完整 rebuild / render-parity 結果見
`revision_audit/presentation_dedup_20261012/package_rebuild_check.json`。

## 本包定位

這是完整、可編譯的論文及既有精簡證據包，不是原 3.16 GB 的 production / restart
archive，也不表示 GitHub 已完成公開 release。較早版本的 notes / audit logs
仍保留作歷史紀錄，其舊頁數與舊建議不取代本輪 README / notes。
