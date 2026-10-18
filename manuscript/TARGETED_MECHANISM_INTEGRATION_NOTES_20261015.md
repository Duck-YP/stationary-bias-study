# 有限度機制補強整合：稿件修訂說明

日期：2026-10-15。**基準是使用者這次上傳的 `manuscript(2).zip`，不是較早的 assistant 版本。**

## 已整合內容

1. **Related Work / 文獻先行性**：加入 Glasgow, Yuan and Ma (2022) 的 iterate-bias 定義及有限步分析脈絡，區分其 SGD-vs-GD trajectory estimand 與本稿 invariant-law global mean。另明確引用 Mangold 的 Lemma 5.1，給予 leading persistent-control covariance 相應 credit。Table 1 不變；沒有把 audit 中的候選係數推導誤寫成前人已完成本稿定理，也沒有聲稱完成全面 novelty 認證。
2. **Introduction / Mechanism**：在非線性 local-iterate bias 的背景句加入 Glasgow 引用，並在 controls 二階矩的解釋中加入來源引用。Contribution list 只追加兩個新檢查的名稱，不增加防守性段落。你這次稿件的摘要、Significance and scope、主定理與證明保持不變。
3. **Section 6.2.5 — Contraction cancellation and covariance-matched noise**：增加一個短小節與主文 Table 4，列出第一座標 matched null、正負 covariance controls、兩種 noise laws 及其 contrast。目標是 paired coefficient 的報告解析度，不將它擴張成每個演算法的零係數或 noise-law invariance 均已認證。
4. **Appendix C.1.4**：给出三角 objective、非零三階張量、完整 covariance intervention、明確係數、對稱／非對稱 bounded laws、模擬及推論設計。保留 imported threshold 與完整 theorem step-size regime 的區別。新研究的 resampling 是各 cell 獨立重抽完整 run vectors，不套用舊設計的 seed-label 聯動規則。
5. **Appendix C.2.5 / Table 12**：補充兩個演算法的兩座標結果與 contrasts，以及 matched 第二座標；主文已列出的 matched 第一座標不重複。36 個 primary scalar summaries 各有一次主要數值呈現。Restricted-grid、單獨算法精度不足、一個第二座標 zero-exclusion 與 temporal diagnostics 均保留。圖表及完整原精度 CSV 在所附 repository materials 中，不需要全部重複印在論文。
6. **Appendix C.3.1**：加入既有 H=4 Cartesian 資料的 raw-minus-balance paired intercept 差（約 -2.39e-7、-2.92e-7）。它排除「只換 estimator 就能消除該組位移」的解釋，不宣称舊 joint-grid discrepancy 已全數解決。

## 主文與附錄分工

- 主文 Table 4：4 個條件的 matched 第一座標 + covariance-matched law contrast。
- Appendix Table 12：個別算法的两座標估計、law/covariance contrasts；matched 第二座標。
- Matched signed-covariance contrast 的兩座標結果放在 Appendix C.2.5 的短式中。
- 所有主表區間均維持原先 36-scalar primary family。Table 12 的數值乘以 10^3 後显示四位小數；主文估計與區間显示八位小數。原始精度、bootstrap variants 與 restricted-grid 全數保留於交付的原始 review ZIP。
- Resolution margins 改稱 coefficient-resolution margins，不使用 predictive/practical-significance band 的措辭。
- 原有 P4 後續研究不加入，原 real-data 分析、歷史 H=4/H=8 與未通過的診斷不改判。

## 保留與核對

- Active source 修改六檔：`references.bib`、`sections/01_introduction.tex`、`sections/02_related_work.tex`、`sections/05_mechanism.tex`、`sections/07_numerical_study.tex`、`appendix/C_numerical_details.tex`。
- `main.tex`（含你這次的摘要）、`macros.tex`、Setting、Main Results、Discussion、Conclusion、Code availability 與 Appendices A/B 位元組不變。
- 13 個原科學表格的 14 個 tabular bodies、78 個原 equation/align environments 與原圖檔、保存資料均完整保留。
- 本輪整合檢查 436 項，0 項失敗；原 saved-result checker 的 1,507 項檢查也無失敗。這是搬移、公式算術、引用與資料保留核查，不是新的 proof audit 或 production reproduction。
- 新增 2 張表，未新增印在稿內的 Figure；九個使用中的原 panels、大小與字級不變。估算最小嵌入文字約 9.66 pt。
- 稿件編譯為 40 頁：主文 19、References 2、Appendices A–C 19。相較上傳稿件（36頁）增加4頁，來自新增的機制檢查、模型與完整數值/敏感性，以及文獻定位。
- 最後編譯沒有 undefined references、duplicate active labels、LaTeX warnings/errors、overfull/underfull boxes。已檢視全部頁面縮圖及新增內容大圖。

## 範圍與使用

**沒有重新模擬、bootstrap、重寫定理、進行新 proof audit，或 push GitHub。** 此次沿用前一輪獨立審閱及提供的 primary-source audit；不額外宣稱核實 DDB 最終出版公式/勘誤。

在 `manuscript/` 執行 `sh build.sh`；Overleaf 使用 `manuscript/main.tex` 為主文件，pdfLaTeX + BibTeX。

`repository_materials/targeted_mechanism/` 保留此次使用者提供的完整結果 ZIP、source ZIP 與前一輪獨立審閱/核查包。這是 GitHub 整理用資料，**尚未發布**；不是主文或附錄內容。原 manuscript 中的其他 supplementary materials 也不變。

`manuscript/tools/check_targeted_table_transcription.py` 可從同包 review ZIP 檢查新增表格的四捨五入轉錄；`tools/check_saved_e4_e5.py` 仍可檢查原有保存結果。均不會啟動訓練。

最終交付驗證：由 ZIP 重新解壓後完整編譯，40 頁文字與 72-dpi 渲染逐頁一致；乾淨重建的編譯記錄沒有排版/引用警告。
