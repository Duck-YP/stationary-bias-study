# SCAFFOLD：研究增量與重要性敘事精修

版本日期：2026-10-10。
基準：`SCAFFOLD_E5_MainText_Revised_20261010.zip`（38 頁）。
修訂後：37 頁；主文 16 頁、References 2 頁、Appendices 19 頁。

## 一、這輪的中心問題

**我們比既有分析多理解了什麼，而這個理解為什麼重要？**

這輪維持 characterization 型理論論文的定位，不將「提出新演算法並改善 test loss」
加入本文的研究承諾，也不引用其他純理論論文來替投稿類型辯護。
主要論述是：兩個方法在共同 leading term 上無法區分的 mean-shift mechanism，
可由明確的 second-order coefficients、共同 remainder 精度與 local second-moment analysis 分開。

## 二、逐檔修改

| 檔案 | 本輪修改 |
|---|---|
| `main.tex` | 摘要重排為問題、研究策略、係數與機制、理論精度及實驗意涵；刪除重複描述。標題、作者及編譯輸入順序不變。 |
| `sections/01_introduction.tex` | 說明 leading-order analysis 留下的是來源辨識問題；homogeneity 的作用是隔離 stochastic-control effect；以 model averaging 解釋研究 mean displacement 的動機。保留一個來源分解公式，減少各段與 contribution list 的重複。 |
| `sections/02_related_work.tex` | 保留兩主題與 theorem-to-theorem comparison 表。明說新增的是 coefficient identification 能力，並保留既有工作的較廣假設範圍。没有增加新文獻。 |
| `sections/04_main_results.tex` | 只修改定理前後的解讀：curvature–noise geometry、client averaging 與 step-size reduction 的差別、control 的 local-step factor、uniform remainder 的辨識用途。定理、推論、命題及全部 displayed formulas 原文不变。命題外增加 samepage 排版包裝，避免 statement 被分頁拆開。 |
| `sections/05_mechanism.tex` | 更清楚解釋「同一 leading global second moment，仍可有不同 stationary mean」的 local-trajectory 原因；公式與推導範圍不变。 |
| `sections/07_numerical_study.tex` | 清楚區分 controlled coefficient tests、E4 的 averaged-model error interpretation、E5 的 directional explanation。保留 E5 在主文，加入指向既有固定 reference-direction comparisons 的簡短說明，沒有新擬合。所有數值、表格、圖形與不相容結果保留。 |
| `sections/08_discussion_limitations.tex` | 以新增的演算法來源辨識能力開場，說明 mean shift、variance、averaging 和 predictive loss 的不同角色；不將缺乏 prediction improvement 當成未完成的承諾。 |
| `sections/09_conclusion.tex` | 總結已增加的理解，而不只再次列舉公式；future directions 保持短小，不要求先完成另一篇研究才能投稿。 |

## 三、保留的科學界線

- E1／controlled experiments 是有限網格上的 quantitative checks，不是全部設定通過的 theorem certification。歷史 H=4 與補充 H=8 的紀錄未變。
- E4 顯示的是 finite-tail mean displacement 在平均模型參數誤差中的相對重要性；沒有將其等同於已獨立辨認的 gamma² control coefficient，也沒有改稱 stationary error floor。
- E5 在主文保留 124 維 directional agreement；同時保留所有六組 magnitude overprediction、2.927 versus 3.5 的 H-ratio，以及 state-dependent noise 的適用界線。
- 參數誤差占比與 absolute task loss 不混用。原本很小的 training-objective difference、未惡化的 test loss、長平均窗口及 diagnostics 全數保留。
- 沒有新的訓練、bootstrap、optimizer fitting、理論延伸或投稿接受率承諾。

## 四、保護與編譯檢查

實際執行的 source-preservation checks：

- Setting、macros、bibliography、四份 Appendix、32 個 figure-directory 檔案、129 個 supplementary-result 檔案逐檔 hash 不變。
- 2 個 theorems、1 個 corollary、1 個 proposition、4 個 lemmas 與 5 個 proof environments 原文不變。
- 67 個 equation environments、8 個 align environments、21 個無編號 display math blocks 原文不變。
- 14 個 table environments、5 個 figure environments、9 個 active panels 保留；所有公式 labels 與引用均有效。
- 沿用獨立 panel PDF＋LaTeX 組版；最小圖中文字約 9.66 PDF pt，未改變嵌入寬度或字體。
- 27 項 preservation／source-reference／build checks 通過。最終 LaTeX log 沒有 undefined references、duplicate labels、warnings/errors 或 overfull/underfull boxes。
- 重新執行既有 compact E4/E5 saved-value checker：1,507 項檢查、221,919 個 scalar comparisons、0 failures，最大差異 1.72e-15。這是保存值的一致性核對，不是新的 independent statistical audit；本輪未重建 batch sums。
- 已檢視 37 頁渲染 contact sheets 與主要修改頁。本文字級、版寬與圖形尺寸不變。

這些檢查確認文字修訂沒有更換數學陳述或實驗證據，不代表本輪重新認證全部證明。

## 五、如何使用

解壓後以 `manuscript/main.tex` 為入口；在 `manuscript/` 執行：

```sh
sh build.sh
```

本輪逐檔 diff、hash manifest、source-preservation JSON、saved-value check、字級表與編譯紀錄位於
`revision_audit/narrative_refinement_20261010/`。
較早的 revision notes、reviewer-risk assessments 和 frozen scientific reports 保留為歷史紀錄，
其中的舊頁數或舊編排建議不代表這輪的最終 presentation。
