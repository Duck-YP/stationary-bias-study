# 有限度機制補強：結果與適用範圍

2026-10-14。已完成限定四篇 primary-source 文獻核查、既有 H=4 Cartesian
資料的 analysis-only audit、獨立模型／noise／kernel 驗證、16 個 paired pilots，
以及凍結後的全部 24 configurations × 12 paired seeds = 288 production runs。
本機 `manuscript` 與歷史研究原始碼未修改，文獻修訂僅提供待審 patch。

**主要結論：paired SCAFFOLD–FedAvg 增量的兩項機制檢查達到預設解析度；
各演算法單獨的第一座標 null 與 noise-law comparison 仍屬精度不足。**
不能將後者的寬區間包含零描述成已驗證零係數或 noise-law invariance。

## 執行與預算

新三角模型採獨立 `trigonometric_chunk`，未沿用硬編碼舊 objective 的
`controlled_chunk`。A=diag(1,2)、alpha=0.05、H=4 固定；四個條件為
rho=-1/4、0、+1/4 的 symmetric law，以及 rho=+1/4 的 asymmetric law。
完整 grid 為 N={64,128} × gamma={1/512,1/1024,1/2048}，每格 12 個獨立
paired runs。算法對共用 indexed noise；不同條件、cell、phase、seed 使用不同
stream。pilot 與 production seeds 不重疊。

每個 run 使用 tau=ceil[1/(0.6 H gamma)]，50 tau burn-in，64 個各長 10 tau
的 batches。此 horizon 是 heuristic，並非已證明的 mixing time。未延長 horizon、
刪除條件或依 target inclusion 調整 estimand／fit。唯一 restricted-grid sensitivity
是預先指定的「移除最大 gamma」，完整 grid 始終是 primary。

新 kernel 的 pilot 實測導出含 25% 餘裕的總成本預估 **1.841 CPU hours**。
實際模擬 chunk 的 process CPU time：pilot **157.531 s**，production
**4544.219 s**，合計 **1.306 CPU hours**，低於六小時上限。此數字累加所有
workers 的 CPU time，不是平行工作的 wall time；checkpoint I/O、分析與單元
測試另計。兩次短 microbenchmark 另合計 0.109 s。
詳見 `ACTUAL_COST_AND_DECISIONS.json`。沒有 RESOURCE_LIMITED 或失敗的
production configuration。

## 模型、解析目標與實作

獨立 symbolic differentiation、Lyapunov 解與精確離散 support 枚舉確認：
全域 0.6 I <= Hess f <= 2.4 I；x*=0；三至五階導數有全域界；T 非零；
C0=I 滿秩且 T[C0]=0；null 的 B11=(-0.0125,0) 並非零。
強凸函數的 gradient 不可能全域有界，這裡的 bounded-derivative 條件是
Hessian 與三至五階，並非宣稱 gradient 有界。

兩種 scalar noise laws 均精確具有 mean 0、variance 1，third moments 為
0 與 1/sqrt(2)，fourth moments 為 1 與 3/2。沒有逐 batch recenter、rescale
或 whitening。正負 covariance 控制的第一座標 B20 分別為：SCAFFOLD
±0.059375、FedAvg ±0.0375、matched difference ±0.021875；rho 正時為負號。
兩座標均完整保留。grid 小於 imported gamma_imp=1/288，但未宣稱所有 theorem
absorption constants 已驗證。

舊有單元測試在新增獨立路徑前後均 **14/14 通過**；新路徑測試 **6/6 通過**，
另有獨立 checker 驗證非零 states、非零 control mean 的保留、explicit-noise
完整 rounds、H=1、deterministic/quadratic、實際 checkpoint/resume 與 pre/post
finite-window identity。新 control arithmetic 是保留原 mean control 的代數改寫，
並非投影。所有 production finite-window checks 的最大 arithmetic-accounted
equation residual 為 **1.34e-20**，換成 normalized coefficient 尺度為
**6.89e-12**；最大觀測 control mean 為 **4.58e-14**。
這些是實作及時間對齊檢查，不能證明 stationarity 或係數定理。

## 機制一：非平凡零係數與正負控制

下表為 paired D=(bS-bF)/gamma² 的 unconstrained fitted intercepts。
區間是整個 36-scalar primary family 的 **approximate 95% simultaneous sampling
intervals**；不含 deterministic grid remainder 或 burn-in error。

| 條件 | 座標 | 估計 | simultaneous interval | 解析 target |
|---|---:|---:|---|---:|
| rho=-1/4 symmetric | 1 | 0.02187859 | [0.02184128, 0.02191589] | 0.021875 |
| rho=0 symmetric | 1 | -0.00002056 | [-0.00006150, 0.00002039] | 0 |
| rho=+1/4 symmetric | 1 | -0.02185115 | [-0.02189536, -0.02180693] | -0.021875 |
| rho=+1/4 asymmetric | 1 | -0.02188179 | [-0.02193153, -0.02183205] | -0.021875 |
| rho=0 symmetric | 2 | -0.00001447 | [-0.00003488, 0.00000594] | 0 |

paired null 的兩座標區間均完整落在 ±0.004375 practical band。
第一座標 paired null 與兩個非零控制區間清楚分開；正負控制的方向與量級
在無約束 fit 下恢復。signed covariance contrast 第一座標為 -0.04372973，
區間 [-0.04378778,-0.04367168]，target=-0.04375。

在 primary full-grid fit 中，個別算法也恢復非零控制的符號，其 simultaneous intervals 包含解析 target；
但點估計不應描述成高精度恢復。例如 rho=+1/4 symmetric 的 SCAFFOLD／FedAvg
估計為 -0.04683248／-0.02498133，相對 targets -0.059375／-0.0375 仍有
可見差異。rho=0 的第一座標估計約 0.00469／0.00471，區間約
[-0.0181,0.0275]，寬於各自 ±0.011875／±0.0075 bands。因此個別算法的
null resolution 為 **INCONCLUSIVE_PRECISION**；不能把 paired 結果推廣成
個別算法零係數已獲同等解析度驗證。

## 機制二：相同 covariance、不同高階 noise moments

以下對比固定 rho=+1/4，方向為 symmetric minus asymmetric。

| Observable | 座標 | 估計 | simultaneous interval | practical margin | 結論 |
|---|---:|---:|---|---:|---|
| SCAFFOLD | 1 | 0.01131363 | [-0.02013516,0.04276241] | 0.011875 | 精度不足 |
| FedAvg | 1 | 0.01128298 | [-0.02016274,0.04272871] | 0.0075 | 精度不足 |
| paired difference | 1 | 0.00003064 | [-0.00003564,0.00009692] | 0.004375 | band 內 |
| SCAFFOLD | 2 | -0.00049711 | [-0.00988633,0.00889212] | 0.011875 | band 內 |
| FedAvg | 2 | -0.00047466 | [-0.00986491,0.00891559] | 0.0075 | 精度不足 |
| paired difference | 2 | -0.00002245 | [-0.00005105,0.00000616] | 0.004375 | band 內 |

可主張 paired increment 的 law difference 在此次 fitted-coefficient resolution
內相容；不能主張兩種 laws 在有限 N、gamma 的 stationary means 完全相同，
也不能主張每個算法的共同係數均已解析。有限 N 的差異可包含 gamma²/N；
不能把全部 law dependence 都稱為 O(gamma³)。

## 不理想結果、敏感性與未解問題

- 36 個 primary scalar summaries 中，26 個狀態為
  SUPPORTS_WITHIN_REPORTED_RESOLUTION，10 個為 INCONCLUSIVE_PRECISION。
  這是逐摘要解析度分類，不是 26 個獨立成功實驗，也不是證明。
- **Restricted-grid sensitivity 保留三個 DISCREPANCY_REQUIRES_AUDIT。**
  rho=+1/4 symmetric 的 SCAFFOLD 第一座標變為 -0.01675171，區間
  [-0.05907084,0.02556741]，target=-0.059375；FedAvg 變為 0.00510137，
  區間 [-0.03721159,0.04741432]，target=-0.0375。兩者 target 都略在
  simultaneous interval 外，且符號不再被解析。SCAFFOLD 的 plus-minus
  covariance contrast 估計 -0.06840058，區間 [-0.11872928,-0.01807187]，
  也略排除 target=-0.11875。三者 Bonferroni-t sensitivity 均包含 target。
  因此個別算法的符號／量級不能稱為對 restricted grid 穩健；沒有將敏感性
  隱藏或替換 primary。導數、noise covariance、active kernel、端點 identity
  與獨立 fit replay 的檢查未找到實作錯誤，但 burn-in、抽樣變異與有限-grid
  描述模型仍無法完全區分。詳見 `validation/POSTPRODUCTION_AUDIT.md`。
- rho=+1/4 symmetric 的 paired 第二座標為 -2.29282e-5，其 full-grid
  simultaneous interval [-4.23409e-5,-3.51552e-6] **排除精確零**，但完整落在
  ±0.004375 band 內。Bonferroni-t sensitivity 包含零；移除最大 gamma 後估計
  -1.37193e-5，simultaneous interval [-3.56447e-5,8.20613e-6] 也包含零。
  所有版本均保留，不能將 practical resolution 結論寫成精確零得到驗證。
- primary balance 的 144 個 first/last-half scalar diagnostics 有 8 個 nominal
  95% intervals 排除零，均屬個別算法；paired D 沒有 nominal 排除。
  未拒絕差異不能建立 stationarity，零星 nominal 排除也不能自行定位 burn-in
  問題。完整 temporal diagnostics 保留，不延長或重選窗口。
- 個別 raw global means 的變異遠大於 balance。raw 是同-run cross-check，
  並未替換 primary estimator。全部 raw grid、fits、區間及 paired raw-minus-balance
  差異均在 CSV。窗口 identity 通過僅排除相應算術／對齊問題。
- 只有兩個 N levels；(1,gamma,1/N) 是有限 grid 的描述模型，並非 exact remainder
  law，不能宣稱已辨識 N-rate。12 seeds 與 bootstrap intervals 仍有小樣本限制。

`results/RESULT_TABLES.md` 與 CSV 列出全部兩座標、full/restricted fits、普通
marginal intervals、approximate simultaneous intervals、Bonferroni-t sensitivity
及所有 practical-band 結果。未調整目標、方向、fit window 或 polynomial。

## 既有 H=4 audit 的結論

原 Cartesian grid 為 N={32,64,128} × gamma={1/128,1/256,1/512}。
108 paired runs 的主窗口資料與最新版稿件完全一致，原 fit 重播最大差
1.39e-17。240 個可取得起終點的 paired windows，其 identity 最大 equation
residual 為 7.69e-16。paired raw/balance fitted-intercept 差只有約 2–3e-7，
因此 estimator substitution 不能消除既有 paired intercept 的位移。

原 primary 和 2x-tail 缺起點、individual noise eta 缺失，無法完整重建各自
identity。原 t interval、percentile bootstrap 與 independent-cell inference 的
target inclusion 在邊界附近不同；這些全數保留。不能預設差異必定是
finite-grid effect。四個數值核心的 frozen hashes 可恢復，但 12 個 frozen
檔案中只有 8 個完整匹配；未冒稱已找回完整歷史 source tree 或 commit。
詳見 `historical_audit/EXISTING_H4_AUDIT.md`。

## 文獻定位與建議稿件敘述

限定核查四篇 primary sources。Glasgow, Yuan and Ma (2022) 已建立
stochastic local-iterate bias、third-order-smoothness 分析及 infinite-client
round-map 觀點；Mangold 的 SCAFFOLD 分析已有 persistent-control covariance。
文獻報告展示其 ingredients 如何經額外 Taylor／stationary reasoning 得到係數
候選；因此不宜宣稱 noise-induced bias 或 control covariance 機制本身首次被發現。
此 bounded audit 未找到指定來源直接建立本稿完整 matched second-order
coefficient 加 N-uniform O(gamma²/N+gamma³) 結論，但並非全面 novelty proof。

建議 paper-facing claims（待後續人工整合，尚未套用）：

> In the controlled trigonometric model, the paired SCAFFOLD–FedAvg coefficient
> separates a nontrivial contraction null from opposite-signed covariance
> controls and shows covariance-matched noise-law differences within the
> prespecified fitted-coefficient resolution. Algorithm-specific null and
> law-difference estimates remain less precisely resolved.

> The matched stationary coefficient and its N-uniform remainder refine prior
> local-iterate bias and stationary control-covariance analyses, rather than
> introducing the underlying nonlinearity–noise mechanism.

文獻修訂位於 `literature/proposed_related_work.patch`，apply-check 已通過但未套用。
DDB 最終 publisher formula／corrigendum 尚未取得核實，來源版本與公式 caveats
在 `NOVELTY_COMPARISON.md` 明列，不將未讀版本假裝已驗證。

## 交付與未執行事項

交付 review ZIP、source ZIP、全部配置／小型 run summaries／CSV／獨立 vector
PDF panels／來源與結果 hashes。checkpoints、primary-source PDFs 的本機位置與
retrieval manifest 一併保留；不需要新增大型 audit archive。

未新增 dataset、未重跑舊 production 或 E4/E5、未擴展 H／參數搜尋、未修改主
論文、未 push GitHub。未證明新模型的 mixing time、未排除 deterministic grid
remainder，亦未解決歷史缺失端點或未恢復的 frozen source 檔案。
