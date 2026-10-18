# 完整整合版：2026-10-10

## 版本基礎

以 `SCAFFOLD_Narrative_Refined_20261010.zip` 為完整底稿，合併最新兩個章節替換包：
`SCAFFOLD_Numerical_Grouping_20261010.zip` 與 `SCAFFOLD_Significance_Framing_20261010.zip`。
這是完整論文專案，不是需要另行合併的 patch。

## 已整合的四份章節

- `sections/01_introduction.tex`：在 contribution list 後加入一次 `Significance and scope`，交代精確 characterization 的性質、理解價值與自然延伸。
- `sections/02_related_work.tex`：Table 1 改以 analytical resolution 比較，明說演算法與 stationary bias 本身未因分析改變；新增與 Section 6.2 的實驗連結。
- `sections/07_numerical_study.tex`：原 6.2–6.5 合併為 `6.2 Controlled tests of analytical predictions`，內有四個 subsubsections；後續 real-data、E4、E5 分別為 6.3、6.4、6.5。
- `sections/08_discussion_limitations.tex`：只替換末段，強調顯式係數作為進一步分析的參考，而不是以 predictive-loss improvement 評價這篇 characterization。

## 完整保留

`main.tex`（包含 Abstract）、Setting、Main Results、Mechanism、Conclusion、Appendices A–D、macros、bibliography、build script 均與 Narrative Refined 底稿位元組相同。
所有定理、引理、命題、證明、displayed equations 和圖形環境未變更。
原 14 張表格中，只有 Table 1 的標題／說明／欄名依已同意版本更新；其他 13 張表格原文不變。
全部圖檔與 `supplementary_results/` 中的保存檔案位元組相同。
Historical H=4、H=8、E4 temporal diagnostics 與 E5 magnitude/local-step discrepancies 的資料及說明皆保留。

## 本輪檢查

- 執行完整 `sh build.sh`（pdfLaTeX + BibTeX + 兩次 pdfLaTeX）。
- 編譯結果 38 頁：主文 17 頁、References 2 頁、Appendices 19 頁。
- 35 項整合／保留／引用／編譯／字級檢查通過；沒有未定義引用、重複 active labels、LaTeX warnings/errors、overfull/underfull boxes。
- 9 個主稿實際嵌入的圖形 panels，最低文字字級約 9.664 PDF pt；此次未改圖形尺寸。
- 已逐頁渲染為縮圖檢閱，並檢視修改位置的大圖；没有為縮頁而改字級、行距或頁邊。

上述為整合與排版檢查，不是新 proof audit，沒有重新執行訓練、統計 resampling 或實驗。
既有 audit files 與 scientific summaries 為歷史紀錄，記錄当時的版本及結論；最新整合資訊以本檔案及 `revision_audit/full_update_20261010/` 為準。

## 編譯

解壓後，进入 `manuscript/` 執行：

```sh
sh build.sh
```

Overleaf 主文件設定為 `main.tex`，使用 pdfLaTeX。包內含 `main.bbl` 與更新後的 `main.pdf`。
主稿仍是既有 article-format 版本，沒有轉換期刊模板；沒有建立新的公開實驗 code release，亦不含原始 3.16 GB 完整模擬／restart archive。
