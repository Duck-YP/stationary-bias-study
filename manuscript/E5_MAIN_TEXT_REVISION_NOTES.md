# E5 主文整合與 significance 論述修訂（2026-10-10）

## 本輪基準與範圍

基準檔為 `SCAFFOLD_Final_E4_E5_20261010.zip` 中的完整 37 頁稿件。
本輪依作者最新決定，將 E5 的 **directional explanatory evidence** 納入主文，
並調整 E4 的重要性敘述。没有新增實驗、重跑訓練、重新估計區間或更改定理。

編譯結果為 **38 頁：主文 17 頁、References 2 頁、附錄 19 頁**。
原字級、行距、頁面邊界、圖檔和嵌入尺寸均未更動；沒有新增 Figure 或 Table。

## 逐檔修改

| 檔案 | 修改 |
|---|---|
| `main.tex` | Abstract 末段加入平均模型誤差組成與 E5 方向一致性；不以 prediction degradation 作為研究成果的必要條件。仍保留 magnitude／local-step scaling 的適用界線。 |
| `sections/01_introduction.tex` | 保留理論問題與機制隔離主線；將第三項 contribution 調整為 numerical evaluation and real-data interpretation，區分 coefficient tests 與 directional evidence。 |
| `sections/07_numerical_study.tex` | 更新章節導言的證據分工；精修 Section 6.7 的 significance 解讀；新增 Section 6.8「Directional agreement beyond the additive-noise model」。 |
| `sections/08_discussion_limitations.tex` | 强調平均前後的參數誤差組成不同，以及 curvature–noise structure 的方向解釋價值；保留 objective／prediction loss 是不同評價量的界線，不再將未發現 predictive harm 寫成主要研究失敗。 |
| `sections/09_conclusion.tex` | 總結理論解析、E4 的 finite-tail parameter-error relevance，以及 E5 的方向連結；不新增 universal performance claims。 |
| `appendix/C_numerical_details.tex` | 將既有 plug-in equation 移至 Section 6.8，保留 `eq:e5-proxy` label 和原公式；補上保存資料已有的 fixed-direction comparators，並保留完整 E5 table、全部診斷與限制。 |

## Section 6.8 的內容

- 先定義 reference-point Hessian、third derivative 與 single-example gradient-noise covariance。
- 展示原來 Appendix C.12 的 plug-in vector，明確說明方向與幅度都沒有對 observed difference 做擬合。
- 在 E5 指定的 `K=64` window，保留全部六個 nonzero-proxy configurations；full-vector comparison 使用全部 124 個座標。
- 主文報告 cosine 點估計 `0.9965–0.9993` 與 observed-to-proxy **norm** ratio `0.718–0.940`。兩者不是 explained MSE fraction。
- 明確報告大小全部被 proxy 高估，以及 matched `H=4/H=2` projected ratio 約 `2.927`，而非 `3.5`。
- 清楚區分方向解釋與 exact control-prefactor validation；state-dependent noise 和 finite-tail 的證據範圍未改變。

## E4 的新定位

E4 回答的是：**systematic finite-tail mean displacement 在平均模型參數誤差中不一定可以忽略**。
它不直接證明真實資料中的全部位移就是 additive-noise theorem 的特定二階 control coefficient。

以下數據與診斷全部維持原樣：68.1%／49.5% mean-displacement shares、實際 averaging budget、
absolute objective／test-loss differences、未達成的 temporal-equivalence／crossover requirements，
以及未與正式資料合併的兩個 extended pilots。

## E5 的編輯定位與歷史報告

E5 的資料、分析方法及 evidence status 沒有改變。改變的是**稿件中的呈現位置與論述重點**：
主文可以介紹有科學資訊的 directional agreement，不需要把它升格成 exact coefficient validation。

`supplementary_results/E5/` 中原始 `BRIDGE_DESCRIPTIVE_ONLY` 結論，以及當時「appendix-first」的
編輯建議，均原樣封存。這些是歷史分析紀錄，不代表本輪仍採用 appendix-only 的呈現方式。
當前編輯決定以本說明及主文 Section 6.8 為準；科學證據界線不變。

## 額外修復

原 ZIP 有兩處文字化而未生成引用的殘留 `Section~` / `Appendix~` + 換行 + `ef{...}`。
本輪修復為正式的 `\ref{...}`，分別指向 `sec:num-averaging` 與 `app:e4-averaging`。
這些是引用排版修復，沒有修改其研究內容。

## 保留與檢查

- Related Work、Setting、Main Results、Mechanism、Appendices A/B、Appendix D、macros 與 bibliography：位元組相同。
- 全部 **14 個既有 table environments**：內容相同。
- 全部 **32 個 figure-directory 檔案**、**129 個 supplementary-result 檔案**：位元組相同。
- 9 個 active panels 的 source PDF、LaTeX 尺寸與字級不變；最小最終文字約 **9.66 PDF pt**。
- `eq:e5-proxy` 從附錄搬至主文，原公式內容相同且只定義一次；後續公式號由 LaTeX 自動更新。
- 重新執行保存值一致性工具：**1,507 組檢查、0 failures**。未重新做 bootstrap 或原始 batch reconstruction。
- 獨立核對新進主文的 E5 range、H ratio，以及附錄的 comparator ranges，與保存 CSV 相符。
- 完整 build 無未定義引用、重複 active labels、LaTeX warnings/errors 或 overfull／underfull boxes。
- 全部 38 頁已渲染；重點檢查 Section 6.7/6.8、Discussion、E4/E5 表格與公式的位置。

這是**稿件修訂與保存值／編譯檢查**，不是新的 proof correctness audit、stationarity certification 或 production experiment。

## 使用方法

解壓後以 `manuscript/main.tex` 為入口；在 `manuscript/` 目錄執行：

```sh
sh build.sh
```

本輪逐檔 diff 與 QA 紀錄位於 `revision_audit/e5_maintext_20261010/`。
根目錄舊 `REVISION_NOTES_20261010.md` 及該子目錄以外的舊 `revision_audit/` 檔案，
保留作前一輪 E4/E5 整合紀錄，不是本輪的頁數或編輯定位。
