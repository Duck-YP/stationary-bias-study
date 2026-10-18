# E4／E5 最終整合修訂說明（2026-10-10）

## 版本與篇幅

基準是本次上傳的 `manuscript(1).zip`，與另傳 `main.pdf` 位元組一致，原稿共 33 頁。不是以較舊工作稿覆蓋此次本機修改。

新版共 **37 頁：主文 16 頁、References 2 頁、Appendices 19 頁**。維持原有 11pt article、頁面邊界與行距，沒有靠縮字压縮頁數。

## 主文

**Abstract／Introduction：** 維持 problem → importance → method → results。補上 averaging stationary iterates 不改變其 mean 的意義，並將 temporal averaging 納入 numerical contribution。摘要不加入 E5 或 H=4/H=8 的診斷流程。

**Section 6.6：** 將 0.50%／0.23% 明確限定為 raw-checkpoint MSE 的 mean-displacement share，避免與 averaged-model MSE 混用。原 allocation 圖、數據、intervals 和 policy table 全部保留。

**Section 6.7：** 新增 E4，交代九個原配置、十二個 paired seeds、七個 nested windows 和共同尾端。主要設定 K=1 已含 1,280 rounds；K=64 含 81,920 rounds，另有 6,400-round burn-in；整條路徑每個演算法為 90,439,680 次 example-gradient evaluations。

主文保留最長尾段 68.1%／49.5% 的 mean-displacement shares、配對 MSE 差異、很小的 absolute training-objective difference，以及 held-out loss 未顯示 harm 的事實。沒有將結果改稱 certified stationary floor。

**Discussion／Conclusion：** 保持精簡，區分 raw-checkpoint variance、averaged-model variance、mean displacement 與 prediction loss。主文對 E5 只有一個標示 descriptive、明說包含 mismatch 的附錄指引。

## 附錄

**Appendix C.11：** 定義 cross-run U-statistic、between-run variance 與 MSE，保留負 U 值、原有 simultaneous intervals、sampling families、overlapping windows、temporal margins、未滿足的 crossover criterion，及兩個未合併的 longer-run pilots。48-seed production 未執行的狀態保留。

**Appendix C.12：** E5 只作 post-hoc reference-point comparison。新增一張六個 nonzero-proxy configurations 的表，保留 amplitude overprediction、8.85%–29.05% relative vector residual、H ratio 2.927 versus 3.5、step-size trend，以及 H=1 zero-proxy 的處理。沒有加入六張探索性圖，也沒有宣稱特定 control coefficient 或一般 heterogeneous theorem 已被真實資料驗證。

**Appendix D：** 補上 E4/E5 provenance、重用同一批 R0 runs 的關係，以及實際可重現資料範圍；沒有自行宣稱程式已公開。移除 D 開頭的強制分頁，避免多出不必要空白。

## 保持不變

- Related Work 與 theorem-to-theorem comparison。
- Setting、Main Results、Mechanism 的 `.tex`。
- Appendices A/B，包含 common lemmas、兩個 main theorem 的證明與 affine translation proof。
- `references.bib`、`macros.tex`。
- 原有十二張 table environments，以及七個重繪 active panels。
- Historical H=4 exclusions、H=8 offsets、H=1 long-horizon arithmetic flags；沒有改判或用新資料覆蓋舊結果。

## 圖表

新增兩個 E4 standalone vector PDFs，由 LaTeX subfigures 並排。沿用原有 serif、配色及 formatting；字級按最終 PDF 嵌入尺寸檢查。

- 原有七個 panels 最小文字約 9.66 PDF pt。
- 新 E4 panels 最小文字約 9.86 PDF pt。
- 正文 nominal 11pt，實測 normalsize 10.95 TeX pt；全部圖符合至少 9pt 的門檻。
- 新圖直接使用保存的 U、V 與 interval columns，不 refit。Symmetric-log 座標保留負值及跨零區間。

## QA

本輪由原 E4 batch sums 重建全部 1,512 個 averaged models；重算 126 列 E4 U/V/MSE 等點估計與 63 組 E5 paired-vector/proxy，並核對保存的 inference-array intervals。

共 **1,508 組檢查、409,407 個 scalar values、0 failures**，最大絕對重算差異為 1.73e-15 以下。這是 numerical consistency check，不是新的統計推論或 stationary certification。

原有 147 個 active labels 全部保留，加入後共 155 個，無重複。公式引用維持 `Equation~\eqref{...}`／`Equations~\eqref{...}`。交付包另有完整 diff、保留檢查、字級檢查、重新解壓編譯與頁面驗證紀錄。

沒有新訓練、optimizer fitting、bootstrap resampling 或新的完整 proof audit。本文維持 focused theoretical characterization，E4/E5 僅增加其支持範圍內的 empirical interpretation。
