# 最終整合後的 reviewer-risk assessment

## 研究定位

本稿以精確的 stationary mean-bias characterization 為主要貢獻：顯式 client-independent second-order coefficient、uniform remainder，以及 matched local/control source decomposition。它不是新演算法或 prediction-performance improvement paper。

以下是根據稿件與保存證據作出的編輯判斷，不是錄取率估計或期刊編輯承諾。

## 已得到改善的問題

**Why homogeneous?** 主文以機制隔離說明 common objective 的作用，並保留 affine objective shifts 的精確 control translation。此命題限定共同曲率、固定 gradient offsets，不稱作一般 non-IID 定理。

**是否只是無關緊要的小誤差？** E4 顯示 raw-checkpoint MSE 中的小 mean-displacement share，不能直接代表 time-averaged output 的誤差組成。最長尾段的參數誤差占比及配對差異具有可辨識訊號。

**是否缺少 real-data interpretation?** R0 allocation 與 E4 averaging 提供受控的真實資料例子，但仍是 shared empirical objective 的凸分類問題，不是 private-client deployment benchmark。

## 仍存在的主要風險

**Significance／generality：** 本稿仍是較聚焦的二階係數理論。提高已解析項的相對占比，並不保證 reviewer 接受其廣泛重要性。

**有限尾段與成本：** E4 主要結果使用 81,920-round averaging window，未滿足預設 temporal-equivalence／crossover requirements。Training objective gap 的絕對差異小，held-out log loss 未惡化，不能稱為有明顯 operational harm 的 stationary floor。

**E5 不提供 control-prefactor identification：** Full-vector directions 接近，但 proxy 均高估 amplitude；H=4/H=2 實測 2.927，不符合 proxy 的 3.5。E5 留作附錄描述性比較，不應升格為主文機制驗證。

**資料可取得性：** 保存 provenance 與數值紀錄不代表已公開完整 supplementary-code release。正式提交時的 availability statement 仍需反映實際存取狀態。

## 投稿決策

MLJ 仍是有根據但有 significance risk 的首投選擇。本輪不建議新增實驗，也不將 E5 視為接受勝算已提高的保證。以已有理論增量及限定的實驗意涵接受審查，比繼續尋找更漂亮的結果更符合既定停損點。

## 本輪界線

本輪完成資料搬移、點估計與保存區間一致性、數學原檔與原圖保留、公式引用、編譯與字級檢查。未重新進行完整 proof audit、外部 novelty audit、production training、optimizer fitting 或 bootstrap inference；亦未核對投稿網站的所有行政要求。
