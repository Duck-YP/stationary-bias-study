# SCAFFOLD：有限度機制補強的獨立審閱

日期：2026-10-15。基準：本次上傳的 `manuscript(2).zip`、`TARGETED_MECHANISM_REVIEW.zip`、`SOURCE_TARGETED_MECHANISM.zip`、scientific summary 與 proposed patch。

## 1. 結論與工作邊界

本轮的新資料提供了可用的、比增加一般資料集更有針對性的證據：在非平凡的三角函數 objective 下，**matched SCAFFOLD–FedAvg increment** 能區分 contraction null 與正負 covariance controls；相同 covariance 的對稱／非對稱 noise laws，則在預設的 fitted-coefficient resolution 內給出相容的 paired increment。這些結論不能擴張為每個演算法的個別二階係數都已被同樣精確地驗證。

我建議結束新實驗，將這次結果精簡整合進現稿，同時補正 Glasgow 與 Mangold control-covariance 的先行性定位。沒有因這次結果而啟動 P4、更多資料集或更大的網格的必要。若日後出現具體的理論或實作錯誤，另行處理那個錯誤；目前的部分精度不足與抽樣區間敏感性本身不構成無限加跑的理由。

本輪只做審閱與獨立重算。**沒有修改 manuscript，沒有套用 patch、重跑 production/pilot、重新選擇估計法、改 confidence-family、推送 GitHub，或重新證明全部定理。** 另做的短軌跡比較是 kernel consistency tests，不是新的 stationary experiment。

## 2. 實际獨立核查範圍

- 核對 review package 中 439 個 manifest entries；三個凍結的 active simulation source files 與 source ZIP 一致。
- 本次 manuscript 的 243 個 baseline-manifest 檔案全部匹配，未發現基準版本錯置。
- 重新執行原 14 項 tests 與新 6 項 tests，全部通過。
- 不呼叫提供的 model/analysis 函式，從 scalar objective 重新進行 symbolic differentiation、Lyapunov solve、bounded-noise moments 及係數計算。
- 用原始 local/server/control 更新式，獨立比較 128 個短 round cases，包含非零 states、非零 incoming control mean、兩種 noise laws、H=1/4、N=5/11。
- 從 **288 組 paired runs ×64 =18,432 組 paired batch summaries** 重建 3,456 列 per-run observables；檢查 metadata、stream keys、batch counts、起終點连续性、raw/balance 及前後半段結果。
- 用獨立 OLS 實作重建 full/restricted grid 的 144 項 scalar summaries，並按凍結的規則重播每個 family 4,000 次 paired-run bootstrap。
- 主要 balance/full-grid estimates 與 interval endpoints 的最大重算差異約 **2.98e-16**。資料搬移與數值運算未發現會改變科學解讀的不一致。
- 檢查新的 finite-window identity：最大 arithmetic-accounted equation residual 約 **1.27e-20**，除以相應 operator 與 gamma² 後約 **6.88e-12**。最大觀測 control mean 約 **4.58e-14**。
- 原 H=4 審閱只从本次交付的 historical per-run sufficient statistics 重播 2,592 個 seedwise fits（7,776 個 terms），沒有重新取得原始大型 archive。最大差異 8.73e-11，出現在包含大尺度 raw coefficients 的比較中。
- 看過八個新主圖 panel 的 PDF 渲染。它們呈現了 paired estimates 的清楚解析度與個別演算法的較寬區間。本輪沒有驗收最終論文中的 figure embedding 或重新排版。

以上是資料、公式、估計與實作的一致性核查，不是完整 proof audit，也不認證 stationarity、混合時間或 deterministic remainder 常數。

### 數值容差透明紀錄

獨立程式使用經尺度化的 OLS 與等價的加權 batch averages，而不是逐行複製原分析。對主要 balance 結果，差異接近 machine precision。raw estimator 在小 gamma 下被 gamma^-2 放大且抽樣誤差很大；其 full-grid simultaneous interval endpoints 的最大差異約 1.80e-7，只有約 7.73e-9 個該列 standard errors。極小 paired standard errors 對共同 max-statistic quantile 的浮點擾動，會傳到較寬的 raw intervals。

最初一律使用過緊的絕對容差，會把這種尺度效應標為 numerical mismatch；核查改用與 standard error 相關的浮點一致性門檻後，沒有實質不一致。**這僅改動核查程式的數值比較門檻，未修改任何實驗結果、bootstrap 規則、CI 或推論標準。** 完整差異記錄在 `inference_comparison_details.csv`。不要將本輪描述為每個浮點位元完全相同。

## 3. 零係數測試為什麼不平凡

令 alpha=1/20，

    f(x)=1/2(x1²+2x2²)
         +alpha[-4(sin(x1)-x1)+sin(x1+x2)-(x1+x2)
                 +sin(x1-x2)-(x1-x2)].

獨立計算得到 A=diag(1,2)，非零三階張量分量為

    T111=1/10, T122=T212=T221=-1/10.

全域 Hessian 下上界為 0.6I、2.4I；x*=0。令 C_rho=diag(1+rho,1-rho)，則

    T[C_rho]=(rho/5,0),
    B11=(-(1+3rho)/80,0),
    B20_FedAvg=(-3rho/20,0),
    B20_ctrl=(-7rho/80,0),
    B20_SCAFFOLD=(-19rho/80,0)                  [H=4].

所以 rho=0 時，objective 非 quadratic、T 非零、C=I 滿秩，卻有 T[C]=0；同時 B11=(-0.0125,0) 非零。這測的是特定 contraction 的抵消，而不是關掉噪音／非線性，也不是要求原始 mean bias 為零。另兩種 covariance 維持 trace(C)=2，讓第一座標的目標符號反轉。

Primary paired fitted intercepts（第一座標；區間為原定 36-scalar family 的 approximate simultaneous 95% sampling intervals）：

| 條件 | Estimate | Interval | Target |
|---|---:|---|---:|
| rho=-1/4, symmetric | 0.02187859 | [0.02184128, 0.02191589] | 0.021875 |
| rho=0, symmetric | -0.00002056 | [-0.00006150, 0.00002039] | 0 |
| rho=+1/4, symmetric | -0.02185115 | [-0.02189536, -0.02180693] | -0.021875 |
| rho=+1/4, asymmetric | -0.02188179 | [-0.02193153, -0.02183205] | -0.021875 |

Null 第一座標的區間最大絕對端點約為非零 target 幅度的 0.281%；並非只是在很寬的 CI 中包含零。第二座標 null 也在预設解析度內。這是有限網格 fitted-coefficient 的解析度，不是精確極限為零的統計證明。

## 4. 相同 covariance 的 noise-law 比較

兩種 scalar laws 分別為 ±1（各 1/2），與 +sqrt(2)（1/3）／-1/sqrt(2)（2/3）。均值都是零、variance 都為一；third moments 為 0、1/sqrt(2)，fourth moments 為 1、3/2。

固定 rho=+1/4，symmetric-minus-asymmetric paired fitted increment 差：

- 第一座標：0.00003064，CI [-0.00003564, 0.00009692]。
- 第二座標：-0.00002245，CI [-0.00005105, 0.00000616]。

兩者均落在事先指定的 coefficient-resolution band ±0.004375。第一座標 CI 的最大绝對端點約為 active target 的 0.443%。這可描述為 paired increment 的 covariance-matched law comparison 在所報解析度內相容。

不能據此說有限 N、gamma 的兩種 stationary laws 或 means 相同。由現有 theorem 可推的 law difference 仍允許 O(gamma²/N+gamma³)。也不能單憑 paired difference 的不變性斷言兩個算法各自不變；相同的個別演算法 shift 可能在差值中抵消。

這裡的 20% bands 是原 protocol 的係數解析度規範，不是 prediction loss、parameter MSE 或 deployment significance 的門檻。建議論文用「prespecified coefficient-resolution margin」，不稱為「practical significance band」。

## 5. 必須保留的未解與精度限制

- Individual null 第一座標的 SCAFFOLD／FedAvg estimates 約 0.00469／0.00471；CI 約 [-0.0181,0.0275]，大於各自解析度 band。因此不能將 paired 成果寫成「兩算法零係數都已驗證」。
- Individual law comparison 第一座標也精度不足。非零 controls primary fits 恢復符號，但 SCAFFOLD/FedAvg 點估計本身不屬高精度係數恢復。
- 去掉最大 gamma 的 restricted fit，保留三個邊界 target exclusions；Bonferroni-t 敏感性包含相應 targets。不同分析方法的抽樣不確定性不能被改寫成全部通過。restricted grid 只有四個 cells、三個 design terms，不能將它當作更精確的確認分析。
- rho=+1/4 symmetric 的 paired 第二座標 primary interval 排除精確零，雖落在解析度 band 內。不同 inference／restricted-grid 結果不一致，故不可宣稱所有零座標都精確獲驗證。
- 144 個 balance temporal scalar diagnostics 中有8個 nominal exclusions，均為 individual algorithms；paired diagnostics 未拒絕差異並不認證 stationarity。
- 只有兩個 N levels；有限 (1,gamma,1/N) fit 不是下一階 remainder 的解析定律。

### 額外的代數核查：第二座標的對稱性

本輪獨立發現並核對 f(x1,-x2)=f(x1,x2)，且原始 updates 對 x2、controls 的第二座標及 noises 同時反號保持等價。對 diagonal symmetric noise 與零初始狀態，理想隨機模型的 finite-time E[x2] 也應為零。因此，這個特定 symmetric-law 第二座標的小幅 sampling exclusion，不宜自動解讀成真實非零 mean 的 deterministic remainder。抽樣／推論波動、偽隨機與浮點效應仍需區分；本輪沒有識別其唯一原因。

這項代數事實不適用於 asymmetric law，也不使第一座標 contraction-null test 變平凡：第一座標仍有非零 B11。這是審閱者的新增解讀，不是凍結研究原先宣告的獨立實驗或成功判準。沒有因此安排更多模擬。

## 6. 原 H=4 問題得到什麼新答案

本次提供的 historical audit 報告指出可取得端點的240 paired windows滿足相應 finite-window identities；本輪從它所附 sufficient statistics 獨立重播所有 seedwise fits，並確認原主要 matched raw-minus-balance intercepts 約為

    coordinate1: -2.39197e-7,
    coordinate2: -2.91783e-7.

這支持：在此已審的 Cartesian dataset 中，單純將 balance 換成 raw mean，不會消除目前的 matched fitted-intercept 位移。

但不能將這句話升格為「已證明原 joint-grid H=4 的差異全部是 finite-grid effect」。原大 archive 未於本輪重開；部分 primary/extended windows 缺起點與 individual noise sums，無法全數重建 individual identities。不同版本／推論的邊界 target inclusion 也不能相互取代。

現稿只需保留具體診斷與其範圍，不需要新增長篇操作紀錄。這項 audit 沒有提供重啟大規模舊實驗的必要理由。

## 7. 文獻定位：有實質先行性，不只是補 citation

本輪重查 Glasgow 官方原文，以及兩份 Mangold 指定 author versions 的相關定義、covariance 與 stationary expansion。Glasgow 已研究 finite-step stochastic iterate bias（SGD 期望軌跡減 GD 軌跡），並分析 third-order smoothness 與 homogeneous/infinite-client 的觀點。Mangold 的 SCAFFOLD Lemma 5.1 已有 explicit persistent-control covariance，其同質化 leading expression 為 (1-1/N)C/H。

報告中把 infinite-client local-round map 做額外 discrete Taylor/fixed-point 展開，可以得到 FedAvg 的候選二階係數；使用既有 control covariance 亦能推導本稿控制项的候選形式。這些是**本次文獻 audit 的追加推導**，不是聲稱 Glasgow 或 Mangold 原 theorem 已經逐字給出本稿的完整結果。

因此，應將 contribution 界定為：在共同模型與同一 N-uniform remainder 精度下，建立 explicit matched stationary second-order characterization，控制其他同階候選項與混合 moment errors。取得候選係數不等於證明任意 joint limit 下的 remainder；先取 N→infinity 也不能取代本稿的 uniform stationary analysis。

這次限定四篇的核對未找到已建立完全相同 matched expansion + N-uniform O(gamma²/N+gamma³) 結論的 theorem，但這不是全面 novelty certificate。不要將所有 ingredients 宣稱為本文首次發現，也不必將「有先行 ingredients」寫成本文僅剩形式性工作。

上傳的 patch 已通過 dry-run apply check。建議採納其 Glasgow paragraph 與控制 covariance 的具體 credit，再作語句精煉；不盲目套入更長的防守段落。Table 1 仍比較 stationary expansions，不混入不同 estimand 的 finite-iterate bounds。DDB 最終 publisher formula 與可能更正仍未於本次成功核實；不將 author-version 的 isolated printed-formula caveats 當成新稿的錯誤，亦不聲稱已核對 final edition。

## 8. 建議的最小稿件整合

1. **Related Work／必要的機制段引用：** 補 Glasgow iterate-bias credit 與 Mangold control covariance precedent；保留核心 novelty 在 matched coefficient resolution + common uniform remainder。不要再新增一段自我辯護。
2. **Section 6.2 增加一個短項目：** “Contraction cancellation and covariance-matched noise”。用一張緊湊表呈現 paired sign/null/law 比較，明確標示 fitted intercept、confidence family，以及 individual null/law precision 尚不足。不需要所有新圖都入主文。
3. **Appendix C：** 放三角模型的可核算定義、noise laws、兩座標完整結果、restricted-grid／temporal diagnostics。主文表不再重列。code、hash、逐run資訊與核查流水帳仍放 repository。
4. **保留現有歷史資料、Figure格式與theorems：** 不覆蓋舊H=4/H=8、不把新結果提升成real-data係數驗證、不加入P4。除發現確切錯誤外，不再開啟另一輪研究。

建議的主文敘述（草稿，尚未套用）：

> The matched coefficient distinguishes a nonquadratic contraction-null case from opposite-signed covariance controls. At fixed covariance, symmetric and asymmetric bounded noises yield paired increments compatible within the prespecified fitted-coefficient resolution. Individual-algorithm null and noise-law comparisons are less precisely resolved.

## 9. Sources and reproducibility for this review

User-provided sources: `SCIENTIFIC_SUMMARY(3).md`; review package's `PROTOCOL_FROZEN.json`, `results/`, `run_summaries/production/`, `validation/`, `historical_audit/`, and `literature/`; source package's `targeted/` and `tests/`.

Primary literature checked:
- Glasgow, Yuan and Ma (2022): https://proceedings.mlr.press/v151/glasgow22a.html and its official PDF, especially Definition 2.1, Theorems 2.4–2.5, Section 2.3.
- Mangold et al., SCAFFOLD, arXiv:2503.07594v1: https://arxiv.org/pdf/2503.07594v1, Lemma 5.1 and Theorem 5.3.
- Mangold et al., FedAvg, arXiv:2412.01389v2: https://arxiv.org/pdf/2412.01389v2, Theorems 3–4.

The attached independent audit bundle retains our scripts, point/interval reconstructions, discrepancies, test logs, and machine-readable summaries. It does not duplicate the full uploaded source, simulation arrays, or manuscript, and does not claim any repository content has been published.
