# SCAFFOLD — 讀者導向的稿件／重現文件分離

基礎版本：SCAFFOLD_Text_Readability_20261012.zip（37 頁）。
本版：35 頁；主文 18 頁、References 2 頁、Appendices A–C 15 頁。

## 已完成

1. 原 Appendix D 的長篇 provenance、seed/commit/artifact 清單，改為 Conclusion
   後一個簡短的 Code availability 段落。編譯稿不再有獨立 Appendix D。
2. 主文、附錄與圖表 caption 中不再使用 E1/E4/E5、R0/R1/R2 等內部開發代號。
   改用 shared-objective setting、disjoint IID partition、disjoint label-skew partition、
   model-averaging analysis、post-hoc directional comparison 等科學描述。
3. 移除正文及附錄中的 CSV/NPZ/JSON 檔名、結果目錄、seed IDs、commit IDs、
   逐檔核查與「共有多少表格列被保存」等實作紀錄。
4. Appendix C 保留研究理解所需的模型、實驗網格、樣本數、burn-in/averaging
   設計、估計方法、區間建構、精度限制與影響解讀的診斷。
5. 直接均值／balance 比較表仍保留四筆例外及其數值，只將 Seed 欄移至 repository 文件。
   真實資料比較表以「Disjoint IID partition」「Disjoint label-skew partition」分組，
   不再使用內部 regime codes。
6. 保留兩組 controlled studies 的區別、兩組 joint-grid H=4 target exclusions、
   Cartesian-grid H=8 discrepancies、temporal-equivalence 未達門檻、長時間 H=1
   arithmetic sensitivity 及 E5 的 H-scaling discrepancy。沒有因去除實作說明而改判。

## Repository 文件

ZIP 的 repository_documentation/ 整理了名稱對照、provenance/reproduction 說明、
被搬出的原文以及前版 C/D 的完整來源快照。原 supplementary_results/、tools/、
圖檔與分析輸入維持原路径，避免破壞重算腳本。

這些是本機整理的 GitHub 待上傳材料。沒有替使用者推送 GitHub、變更權限或驗證公開
release。Code availability 沿用原稿的 companion repository 地址；投稿前需將相應
程式、設定、數值記錄與文件發布／確認可取得，不能把既有 7f6de2c 誤稱完整 supplementary release。

## 保留與檢查

- Introduction、Related Work、Setting、Main Results、Mechanism、Discussion、Conclusion、
  Appendices A/B、bibliography、macros 原文保持不變。
- 主文及 Appendix C 的 displayed equation/align blocks 不變。
- 13 張科學表格的數學欄位逐項比對相同；只移除內部 seed identifiers 和重新命名資料分組。
- 全部 figure assets、supplementary_results、tools 與原檔逐位元組比對相同。
- PDF 掃描：沒有可見 E0–E5/R0–R2 開發代號、結果檔名、結果目錄或指定的 seed/commit IDs。
- 205 項靜態保存／命名檢查通過。
- 執行既有 saved-result checker：1,507 項檢查、221,919 個 scalar comparisons、0 failure。
  最大絕對差 1.7208456881689926e-15。這不是新訓練、bootstrap、batch 重建或 proof audit。
- 最終編譯無 undefined references、重複 label、LaTeX warnings/errors、overfull/underfull。
- 35 頁已渲染檢視。尚未進行下一階段的 Figure labels 重繪或整體浮動位置優化。

## 編譯

在 manuscript/ 執行 `sh build.sh`。Overleaf 以 main.tex 為主文件，使用 pdfLaTeX。
新的簡短來源段落位於 sections/10_code_availability.tex。
