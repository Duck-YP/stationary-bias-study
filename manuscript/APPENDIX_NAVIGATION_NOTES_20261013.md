# SCAFFOLD：Appendix C 導航與實驗表述整合修訂

日期：2026-10-13  
基準：`SCAFFOLD_Editorial_Polished_20261013.zip`  
目前 PDF：36 頁（主文 18 頁、References 2 頁、Appendices A–C 16 頁）。

## 本次範圍

只修改兩個有效稿件來源：
- `manuscript/sections/07_numerical_study.tex`
- `manuscript/appendix/C_numerical_details.tex`

Introduction、Abstract、Related Work、Setting、Main Results、Mechanism、Discussion、Conclusion、Code availability、Appendices A/B、macros 與 bibliography 均保持原樣。沒有新實驗、重新 bootstrap、重新解算係數或新的 proof audit。

## Appendix C 的四個主題

### C.1 Controlled experimental design and inference
- C.1.1 Controlled instances and estimation
- C.1.2 Joint-grid simulation and inference
- C.1.3 Cartesian-grid and local-step protocol

### C.2 Coefficient estimates and finite-grid diagnostics
- C.2.1 Joint-grid coefficient intervals
- C.2.2 Matched H=4 finite-grid diagnostics
- C.2.3 Fixed-step and five-dimensional results
- C.2.4 Leading-coefficient and restricted-grid sensitivity

### C.3 Estimator and structural consistency checks
- C.3.1 Direct–balance estimator checks
- C.3.2 Orthogonal coordinate equivariance
- C.3.3 Affine translation and update identities

### C.4 Real-data analyses and diagnostics
- C.4.1 Objectives, partitions, and allocation estimands
- C.4.2 Run-length sensitivity
- C.4.3 Finite-tail model averaging: protocol, estimators, and diagnostics
- C.4.4 Post-hoc directional comparison

原 C.8 的 protocol、coefficient sensitivity 與 affine checks 按功能分置 C.1.3、C.2.4、C.3.3；原 C.10 的 controlled estimator、arithmetic checks 與 run-length checks 分置 C.3.1、C.3.3、C.4.2。沒有把這些內容重複貼到多處。

## 主文與 captions

1. Section 6 原來的證據定位句替換為明確的章節導航：Section 6.2 是 controlled additive-noise coefficient predictions；Sections 6.3–6.5 是 natural-minibatch finite-tail mean displacement 與 directional structure。未新增重複的限制段落。
2. Table 2 caption 明說是 finite-grid extrapolated intercepts，並直接指向 Table 6（C.2.1）的 simultaneous intervals。
3. Section 6.2.2 直接引用 Table 7 與 Figure 5（C.2.2），描述網格點 residual 隨 gamma+1/N 的近似線性趨勢。保留 target exclusions 與 gamma=1/N 的不可分離性；沒有聲稱 fitted-intercept discrepancy 已由一個已知的數值 remainder bound 完全解釋。
4. 5D、leading-coefficient 與 affine 檢查增加對應的表格或小節引用；由 LaTeX labels 自動更新。
5. Figure 3 caption 標明 finite-tail mean displacement；Table 5 caption 標明 post-hoc comparison of finite-tail mean differences。Figure 4 與 Table 4 原有標記保留，未再加長。
6. Seed-block 說明補上 resampling unit：整組 run-level grid vector，matched algorithm pair 一起重抽，不把 chain 內觀測值當成獨立樣本。
7. Table 3 的 H=8 列、數值與區間完全不變；沒有用 H-dependent constants 代替對其誤差來源的識別。

## 保留與驗證

- 全文 13 個科學表格的數值內容未改；表格順序變動使 leading-coefficient 表成為 Table 10，direct–balance 表成為 Table 11，相關引用自動更新。
- 兩個修改檔內的 15 個 numbered mathematical environments、4 個 unnumbered displays 與全部 13 個 tabular bodies（其中一張表有兩個 tabular）逐一比對不變。
- 32 個 figure-directory files、132 個 supplementary-result files 均與基準位元組一致。9 個使用中的 panels 及嵌入尺寸沒有修改。
- 所有原 labels 均保留；新增主題層的 labels。有效正文中的 98 個 reference targets 全部可解析，沒有重複 label。
- 完整 pdfLaTeX/BibTeX 編譯成功；final log 沒有 undefined references、multiply-defined labels、warnings/errors 或 overfull/underfull boxes。
- 圖面未重繪；本次未進行全面浮動位置／圖形標籤的 presentation pass。新階層與短導航使 PDF 比基準增加一頁，未用縮小字體或刪除證據壓頁。

## 使用

在 `manuscript/` 目錄執行 `sh build.sh`；Overleaf 設定該目錄的 `main.tex` 為主文件，使用 pdfLaTeX。

`repository_documentation/` 保留既有操作文件，並新增 `APPENDIX_SECTION_MAP_20261013.md`。這些文件沒有出現在 typeset manuscript，也沒有被推送 GitHub。已有的其他日期 notes 為歷史記錄，請以此份修訂說明與現行 README 為準。
