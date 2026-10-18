> Public export context: paths below are adapted from the local revision record. Use ../docs/FIGURE_REPRODUCTION.md for the portable commands. The release-unchanged statement and source guard describe the preceding layout task, before this separately authorized synchronization. Full-page PNG render sets and workspace-baseline audit rerun dependencies remain in the local handoff; the public export includes the compiled baseline, current PDF, vector comparison and saved QA receipts.

# 圖形來源與重現紀錄

日期：2026-10-18。本文追溯本次定稿的 5 張圖、9 個獨立 panel；所有路徑除另註外均相對於專案根目錄。

本次排版基準是由 V2 原始碼乾淨編譯的 **41 頁** PDF，不是 V2 ZIP 內較舊的 PDF。最終檢查對象為 `manuscript/main.pdf`，共 **40 頁**，SHA-256：

```text
81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c
```

這次只調整繪圖呈現、caption 與 LaTeX 版面。未重跑 simulation、training、optimizer、bootstrap 或 regression；未重新估計係數、信賴區間或理論目標。原始研究資料與研究程式未修改。

## 一、繪圖程式與執行方式

| 圖形 | 繪圖程式 | 數值來源根目錄 |
| --- | --- | --- |
| Figures 1、2、3、5，共 7 panels | `manuscript/tools/figure_layout/redraw_figures.py`；共用樣式 `figure_style.py` | **公開匯出對應位置** `artifacts/canonical_paper_export/figure_redraw`，其中含 10 個 `inputs/*.csv` |
| Figure 4，共 2 panels | `manuscript/tools/plot_e4_for_manuscript.py` | `manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv` |

以下命令從專案根目錄執行。`python` 應指向能載入本專案 NumPy、pandas、Matplotlib 相依套件的 Python 3.12 環境；繪圖另需 TeX 的 `latex`、`dvipng`、T1 font encoding 與 Latin Modern。兩個 renderer 均使用 TeX 文字，不以其他字型靜默替代。

```powershell
python manuscript/tools/figure_layout/redraw_figures.py --input-root artifacts/canonical_paper_export/figure_redraw --output manuscript/figures/redrawn
python manuscript/tools/plot_e4_for_manuscript.py
```

第一個命令產生 7 組 PDF、PNG、CSV sidecar、幾何紀錄與 `data/provenance.json`；第二個產生 2 組 PDF、PNG、CSV sidecar 與 `data/e4_provenance.json`。E4 程式的輸出路徑由其所在 manuscript 目錄決定，沒有另外的 `--output` 參數。若要保留現有檔案，應在工作副本重現；僅複製 `manuscript/` 並不包含第一個命令所需的外部 frozen input 目錄。

這裡的「fit」是讀取已保存的係數或曲線；例如計算 `beta0 + beta1 * delta` 只是將保存的直線畫出，並未再次擬合。

| 程式 | SHA-256 |
| --- | --- |
| `manuscript/tools/figure_layout/redraw_figures.py` | `3a9eb7e7683059c18b90ff69c58b4ccda0db07449f0353d3cab0415b2b295ed2` |
| `manuscript/tools/figure_layout/figure_style.py` | `e34844f6238a834ff8f27bf7d3232b03b7a173f22ac7b52571364eaa92f798e0` |
| `manuscript/tools/plot_e4_for_manuscript.py` | `2a348071a7b16578ab4ee223c1a607ac79927ea05a9652c7f7bf0b412ebb9b19` |

## 二、9 個 panel 的輸出及論文位置

下表每個名稱均對應 `manuscript/figures/redrawn/<名稱>.pdf` 與同名 PNG；其逐筆繪圖資料為 `manuscript/figures/redrawn/data/<名稱>.csv`。頁碼適用於上述指定 SHA-256 的最終 PDF。

| 圖／panel 名稱 | 內容 | LaTeX 位置及 figure label | 最終頁碼 |
| --- | --- | --- | ---: |
| 1(a) `hist_matched_H2` | Matched coefficient，H=2，兩座標 | `sections/07_numerical_study.tex`：`fig:num-matched-primary` | 11 |
| 1(b) `hist_matched_H4` | Matched coefficient，H=4，兩座標 | 同上 | 11 |
| 2(a) `hist_fixed_gamma_coord1` | 固定步長、座標 1 | `sections/07_numerical_study.tex`：`fig:E-p2-plateau` | 12 |
| 2(b) `hist_fixed_gamma_coord2` | 固定步長、座標 2 | 同上 | 12 |
| 3 `real_R0_allocation` | R0 client/minibatch allocation | `sections/07_numerical_study.tex`：`fig:real-allocation` | 15 |
| 4(a) `e4_averaging_scaffold` | SCAFFOLD 時間平均後的 U、V | `sections/07_numerical_study.tex`：`fig:e4-averaging` | 16 |
| 4(b) `e4_averaging_fedavg` | FedAvg 時間平均後的 U、V | 同上 | 16 |
| 5(a) `hist_H4_smallstep` | H=4 smaller-step path，兩座標 | `appendix/C_numerical_details.tex`：`fig:E-control-h4`／`fig:E-h4diag` | 32 |
| 5(b) `hist_H4_loglog_residual` | H=4 全部九個 grid points 的絕對殘差 | 同上 | 32 |

LaTeX 檔案路徑在本表相對於 `manuscript/`。配對 panels 使用 `0.49\textwidth`；Figure 3 使用 `0.58\textwidth`。每個 PDF 均只有一個 scientific axes。

## 三、精確來源欄位與選取規則

下列 `inputs/...` 路徑均位於 `artifacts/canonical_paper_export/figure_redraw/`。歷史 CSV 的 `coordinate=0,1` 對應圖中的座標 1、2。

### Figure 1：matched H=2／H=4

- 觀測值：`inputs/p3_primary/paired_setting_summary.csv`，分別篩選 `H=2` 或 `H=4`，每個座標保留全部 5 點。橫軸讀 `delta`，縱軸讀 `D_mean`；誤差棒直接使用 `simultaneous_ci_low`、`simultaneous_ci_high`。
- 擬合及截距：`inputs/p3_primary/paired_fit_summary.csv` 的同一 H／座標列。開放菱形位於 `x=0, y=beta0`，截距區間讀該列的 `simultaneous_ci_low/high`。點線在 `0` 與所有保存的 `delta` 上畫出 `beta0 + beta1 * delta`。
- 水平理論線：fit summary 中的 `B20_ctrl_component`。原始 observation summary 亦保存同名目標欄位，sidecar 保留其逐列來源。
- 圖上 pointwise bars 與 fitted-intercept bars 沿用各自保存的 simultaneous Student-t／seed-block-bootstrap 區間；沒有互換或重新計算。

### Figure 2：固定步長的 client-count 比較

- 觀測值：`inputs/p2_plateau/setting_summary.csv`，只取 `estimator=stationary_mean_balance` 與該 panel 的座標，保留全部 5 點。橫軸 `inverse_N`；縱軸 `C_mean`；區間 `simultaneous_ci_low/high`。
- 擬合截距與理論線：`inputs/p2_plateau/plateau_fit_summary.csv` 的 `beta0`、截距 `simultaneous_ci_low/high`、`B20_component`。
- 已存曲線：`inputs/p2_plateau/plateau_fit_curve.csv` 的 `inverse_N`、`fitted_value`；另接上 `x=0, y=beta0`。沒有將 observation 重新回歸。
- `C_mean` 是扣除共享一階項後、除以步長平方的 normalized mean-bias remainder。水平線是 joint-limit reference；固定步長資料不被重新標成該極限的精確實現。

### Figure 3：R0 allocation

- 來源：`inputs/supplement/E3_allocation_signed_projection.csv`。保留 `regime=R0`、`roles` 包含 `allocation`、`H=4`、`gamma=0.1/0.51` 的兩演算法六列，allocation 為 `(N,m)=(8,32),(32,8),(128,2)`。
- 縱軸：`signed_projection * 1000`；誤差棒：**`ci_lower/ci_upper`** 同乘 1000，沒有改用 `adjusted_ci_lower/adjusted_ci_upper`。這是原圖既有的 nominal 區間選擇。
- 橫軸是三個 allocation 類別。SCAFFOLD／FedAvg 圖形位置使用既有的 `-0.045/+0.045` category offset，僅用於分開標記，不代表新的 N 值。
- 此 panel 沒有擬合線或理論 target。

### Figure 4：E4 temporal averaging

- 來源：`manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv`，只取 `cell_id=E3_R0_p0_H4_N128_g0.196078431373`，依 `algorithm=SCAFFOLD/FedAvg` 分為兩圖。
- 每圖原樣保留 `K=1,2,4,8,16,32,64`；橫軸直接讀 `K`。兩條曲線讀 `U`、`V`，區間直接讀 `U_lower_simultaneous`、`U_upper_simultaneous`、`V_lower_simultaneous`、`V_upper_simultaneous`。這些是保存的 E4 196-statistic primary family 的 approximate simultaneous 95% 區間。
- 無 fit、target 或新估計量。連線只連接保存的點。兩圖共用 `xscale=log(base=2)`、`xlim=[0.8,80]`、`yscale=symlog(base=10,linthresh=1e-5,linscale=0.75)`、`ylim=[-5.5e-5,5e-4]`，皆與原圖相同。
- 負的 sampling-corrected U 不截成零。SCAFFOLD 有 3 個 U 區間跨零；FedAvg 有 4 個，且 K=1 的 U 點估計為負。全部保留。兩圖共 28 個觀測點、56 個區間端點，均在顯示範圍內。

### Figure 5：H=4 finite-grid diagnostics

- (a) 觀測值：`inputs/p3_smallstep/paired_setting_summary.csv`，`H=4`，每個座標全部 4 點；讀 `delta`、`D_mean` 與 `simultaneous_ci_low/high`。
- (a) 擬合、截距及 target：`inputs/p3_smallstep/paired_fit_summary.csv` 的 `beta0`、`beta1`、截距 `simultaneous_ci_low/high` 與 `B20_ctrl_component`；繪製方式同 Figure 1。
- (b) 來源：`inputs/p3_diagnostic/pointwise_diagnostics.csv`，每座標全部 9 點。橫軸 `delta`，縱軸 `abs(e_Delta)`，使用 log–log 座標。來源已存 `D`、`B_ctrl` 與 `e_Delta`；renderer 直接讀取既有殘差，不重新估計 target。
- (b) 連線只連接既有殘差觀測，**不是新增的擬合趨勢線**，此 panel 沒有新增 CI。程式另讀 `inputs/p3_diagnostic/scaling_summary.csv` 並記錄其 hash；`loglog_slope`、`loglog_intercept` 等保存的 scaling summary 未用來重估或新增圖上趨勢。論文中的既有 slope 表值保持不變。

## 四、來源檔案 SHA-256

下列 10 個 input hash 已與本次實際輸入檔案及 `manuscript/figures/redrawn/data/provenance.json` 核對一致。E4 另列完整來源路徑。

| 來源檔案 | SHA-256 |
| --- | --- |
| `inputs/p3_primary/paired_setting_summary.csv` | `00e0a848340f2f50b27909aa6b6d2252941cdccc7273b02e4463c670f99195b5` |
| `inputs/p3_primary/paired_fit_summary.csv` | `91be94dbfaeb6c6d280f38e00a76353153ba665211ee3ffa3fbb4b858382b52d` |
| `inputs/p2_plateau/setting_summary.csv` | `f88ff5580373c123862718a18e6e1fa72a258b02a73e43c4e3d4c14f2608a0a2` |
| `inputs/p2_plateau/plateau_fit_summary.csv` | `baafa9b4ff2e6168bbe74b3632029e416ea68e3af61b30b12bb0fccbd2553f5f` |
| `inputs/p2_plateau/plateau_fit_curve.csv` | `3ca61f251e4f84bd69e0b918faa58fff2b10ba0fa2b3d8752ea3432331620866` |
| `inputs/supplement/E3_allocation_signed_projection.csv` | `23b5f53672035f3b9ee0742b44490887db283a2ff66047c4336320e35d8b9cdf` |
| `inputs/p3_smallstep/paired_setting_summary.csv` | `4c85af50d46a86091d03c55707279d34b982900ffefc18b534271733082cda82` |
| `inputs/p3_smallstep/paired_fit_summary.csv` | `12c4bd2184506078742d211d8f3ae70bbf9399651323b9140a09a0e816080e21` |
| `inputs/p3_diagnostic/pointwise_diagnostics.csv` | `044d61e6a93b5bcfa8aabc4028b59242aab1dca28829f8817503ba33a050b546` |
| `inputs/p3_diagnostic/scaling_summary.csv` | `4a5f47c8b260279c9f440114a5700b2938d0f4f1bac3ee8244a969629a70c6d0` |
| `manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv` | `0a403edf7cb6f0b32b5fba70896c186f7aece60f51af8ed11a5c4ab6a0b93c66` |

歷史 7-panel sidecar 記錄 `source_file`、`source_sha256`、`source_row`、原始／顯示值、CI 欄位、target 欄位與保存的 `beta0/beta1`；因此可追溯至 CSV 的實際資料列，而非從圖像反推數字。E4 sidecar 保留完整選取條件、K、U/V 與區間端點，來源 hash 另載於 `data/e4_provenance.json`。

## 五、數值保全與最終 PDF 檢查

本次 QA 的基準、逐項結果與限制在 `docs/figure_audit/layout_20261018/INDEPENDENT_QA_REVIEW.md`。主要可機讀紀錄如下：

| 紀錄 | 已核對的範圍 |
| --- | --- |
| `qa/NUMERIC_INVARIANCE.json` | 226 項檢查通過；9 份 sidecar 與乾淨 V2 基準逐位元組相同，含歷史 124 筆繪圖 records 與 E4 14 列 |
| `qa/historical_authority/NUMERICAL_AUDIT_SUMMARY.json` | 既有獨立 verifier 對 10 個 frozen input CSV 重核 2,646 項，無失敗 |
| `qa/ARTIST_GEOMETRY_CHECKS.json` | 190 項 actual-artist 檢查通過；歷史 7 panels 的觀測、fit、target 與 CI 端點符合 immutable sidecars，並位於 axes 內 |
| `e4_qa/E4_PANEL_QA.json` | E4 來源 hash 不變；兩 sidecar byte-identical；負值、跨零區間、完整顯示範圍均保留 |
| `qa/SOURCE_HASH_GUARD.json` | 原始 1,705 檔 registry 的保全檢查；23 個完整 table environments 不變，研究 source／公式與 figure 外科學文字受保護 |
| `qa/FINAL_PDF_FONT_AUDIT.json` | 適用於本文開頭 SHA-256 的 40 頁 PDF；9 個實際嵌入 panel 全數通過文字、字型、vector 與裁切檢查 |
| `qa/VECTOR_DRAWING_BOUNDS.json` | 包含 stroke padding 的 vector 路徑均位於 panel canvas 範圍內 |

本表 `qa/`、`e4_qa/` 均相對於 `figure_layout_revision_20261018/`。最終實際嵌入文字最小為約 **9.7000 TeX pt**，E4 約 **10.0002 TeX pt**；測量包含文字矩陣、旋轉與 LaTeX inclusion scaling，不是只讀 plotting script 的字級設定。所有 9 個 PDF panel 都有嵌入字型、保留向量路徑，沒有 raster image layer。

CI 的方法、端點、截距、target、座標與既有 display scaling 均未修改。數值保全與版面檢查證明本次呈現忠於保存資料，不另構成理論正確性、stationarity 或 target inclusion 的新證明。本次沒有修改 `release/`，也沒有上傳或 push GitHub。
