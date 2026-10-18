> Public export context: paths below are adapted from the local revision record. Use ../docs/FIGURE_REPRODUCTION.md for the portable commands. The release-unchanged statement and source guard describe the preceding layout task, before this separately authorized synchronization. Full-page PNG render sets and workspace-baseline audit rerun dependencies remain in the local handoff; the public export includes the compiled baseline, current PDF, vector comparison and saved QA receipts.

# 圖形與版面修訂紀錄 — 2026-10-18

本次僅修訂五張圖的呈現、圖說與 LaTeX 浮動位置。科學正文、定理、證明、公式、實驗設定、表格、估計值、擬合係數、理論目標與信賴區間均保持原樣。未執行實驗、抽樣、重新擬合或重新估計區間。

## 基準與交付版本

- 比較基準：從最新 V2 原始碼乾淨編譯的 **41 頁** PDF，位於 `../docs/figure_audit/layout_20261018/BASELINE_main.pdf`，SHA-256 `9b005005254f025caee170df75bd3efc95b188fd519cf217aca548b23673ead0`。
- V2 壓縮檔隨附的 PDF 是較舊的 40 頁成品，另存為 `../docs/figure_audit/layout_20261018/SUPPLIED_OLDER_main.pdf`，沒有拿它作為此次版面比較基準。
- 交付版本：本資料夾的 `main.pdf`，**40 頁**，SHA-256 `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`。完整編譯副本及紀錄位於 `../docs/figure_audit/layout_20261018/`。

## 各圖修改

全部五張圖、九個面板均已重新輸出向量 PDF；圖 3 僅作必要的標籤及字型一致化。

| 圖 | 基準 → 新版頁碼 | 呈現修改 |
|---|---|---|
| 1：matched H=2/H=4 | 12 → 11 | `Saved fit` 改為 `Finite-grid fit`；圓點／空心方塊表示觀測值，點線表示既有線性擬合，虛線表示理論目標，空心菱形表示擬合截距。保留全部誤差棒及原有座標範圍。 |
| 2：fixed-step client count | 13 → 12 | 縱軸改為 `Normalized mean-bias remainder`；圖說明確連結式 (33) 的統計量及固定步長與 joint-limit target 的區別；採用與圖 1 相同的觀測、擬合、目標及截距標示。 |
| 3：real-data allocation | 15 → 15 | 明示 signed projected mean displacement 的 ×1000 比例與橫軸 `(N,m)` 配置；保留三個配置、六個估計值、誤差棒及既有分類座標位移。 |
| 4：temporal averaging | 17 → 16 | 明示 squared mean displacement (U) 與 averaged variance (V)，以圓點／空心方塊及實／虛線區分；保留相同的 symmetric-log 軸、線性區間、座標範圍、負估計值與跨零區間。 |
| 5：H=4 diagnostics | 32 → 32 | smaller-step 面板統一觀測／點線擬合／虛線目標／菱形截距；log–log 面板強化座標及標記可讀性，仍連接原有殘差觀測值，沒有新擬合趨勢線。既有斜率保留在未修改的表 12。 |

九個面板使用嵌入字型及向量文字、標記與線條。最終論文內面板文字的有效最小字級約為 9.7 pt；E4 為 10.0 pt。這是從 PDF 文字及縮放矩陣量測的結果。主文、圖說及其數學上下標沿用既有 LaTeX 字型設定。

## 浮動位置與留白

- 保留 11 pt 主文及所有表格內容、字級和間距。
- 在數值研究章節起設定 `topnumber=3`、`bottomnumber=2`、`totalnumber=4`，以及 `topfraction=0.90`、`bottomfraction=0.80`、`textfraction=0.08`、`floatpagefraction=0.75`。讓相關圖表與文字共享頁面，減少稀疏的獨立浮動頁。
- 圖 1、2、3、5 採用 `[!htbp]`；圖 4 原本即使用該設定。移除 contraction/noise 小節之前的一處 `\FloatBarrier`，保留進入 real-data、E4、E5 各實驗區段的界線。
- 七個歷史面板高度由 3.50／3.25 in 統一至 3.12 in；兩個 E4 面板由 3.50 in 改為 3.25 in。保留論文中的面板寬度及可讀字級，以調整圖內空間改善排版。
- 圖 2 現位於第 12 頁，與自己的實驗設計、解讀及後續小節連續排版。圖 5 第 32 頁現在緊接相關表格與文字，原先浮動頁的大幅留白已消除。
- 圖 1 第 11 頁及圖 4 第 16 頁更接近對應討論；附錄後段的圖表流動也因相同浮動設定改善。頁數減少是重新排版的結果。
- 未使用負 `\vspace`、縮小全域字型或強制定位套件。

## 數值與內容保全

- 九個繪圖 CSV sidecar 與基準逐位元組一致：歷史圖 124 筆、E4 14 筆來源紀錄。
- 歷史來源獨立驗證器 2,646 項檢查全部通過；另有 226 項數值核對、190 項實際繪圖物件幾何核對全部通過。
- 檢查內容涵蓋觀測座標、理論目標、擬合截距、保存的擬合曲線、信賴區間端點、原有縮放與分類位移；E4 的負值及跨零區間均保留。
- 所有 23 個完整表格環境保持原樣。排除圖說與明確的浮動控制後，科學正文一致；定理、證明、公式與原始實驗結果檔保持原樣。
- 1,705 個原有檔案的雜湊清單用於變更範圍核對，其中 `release/` 的 1,435 個登錄檔案全部未變。沒有 push 或上傳。
- 詳細獨立檢查見 `../docs/figure_audit/layout_20261018/INDEPENDENT_QA_REVIEW.md` 與同資料夾 JSON；來源與命令見 `FIGURE_PROVENANCE.md`。

## 編譯與視覺核查

遵循既有 `pdflatex → bibtex → pdflatex → pdflatex` 流程，從乾淨的完整稿件副本編譯，使用 `-halt-on-error -file-line-error -no-shell-escape`。沒有未解引用、重複標籤、overfull box 或缺圖。唯一警告是基準即存在的 `epstopdf` 提示：shell escape 未啟用；沒有新增警告。

基準全部 41 頁與新版全部 40 頁均已渲染。已檢查全稿 contact sheets、五張圖所在整頁、九個面板彩色及灰階預覽；未見圖說分離、圖文重疊、裁切或孤立小節標題。PDF 字型嵌入、向量路徑、畫布界線及誤差棒位於座標範圍內的檢查均通過。

前後比較位於 `../docs/figure_audit/layout_20261018/BEFORE_AFTER.pdf`，附來源索引。基準與新版每頁 PNG 分別保留在 `baseline/rendered/` 與 `final/rendered/`。文字差異及檔案雜湊清單見 `../docs/figure_audit/layout_20261018/FIGURE_LAYOUT_REVISION.patch`、`CHANGE_MANIFEST.json`。

## 剩餘作者判斷

第 18 頁的結論尾段、第 20 頁的參考文獻尾段及第 40 頁的附錄末頁仍有自然的章末留白。既有參考文獻／附錄分頁界線保留；此次沒有為追求頁數而壓縮文字或改動科學內容。沒有待補繪圖資料或阻止編譯的問題。是否進一步改採期刊專用模板，留待作者另行決定。
