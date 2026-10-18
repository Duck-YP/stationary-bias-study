# SCAFFOLD/FedAvg 補充實驗 Codex 任務包

## 使用方式

將 `CODEX_PROMPT.md` 提供給 Codex，貼上 `START_HERE.txt` 啟動。完整規格已自足，不需要原始實驗 code，也不要求先讀取整篇論文。

本次交付的是**實驗執行規格**，沒有附上已實作的 research engine，沒有執行 simulation，沒有產生新 scientific results。

## 工作範圍

- **E0**：從零重建演算法並驗證 implementation。
- **E1**：分開 H、gamma、N，檢查 leading 與 control coefficients 的不同依賴性。
- **E2**：affine objective heterogeneity 的 exact control-shift relation。
- **E3**：a9a 真實資料上，固定 global objective 的 allocation/update-policy implication experiments。

E3 同時區分 shared empirical-objective diagnostic、disjoint IID partition 及 disjoint label-skew partition。前者是控制實驗，後兩者是模擬 federated data；都不冒充真實生產部署或一般 heterogeneous theorem。

## 優先顺序

Implementation tests 後，controlled 與 real-data 都先 pilot。Pilot 與 production seeds 分離，production 前凍結 protocol。主研究先使用一個真實資料集；不要求立即擴張成大型 deep-learning benchmark。

若資源受限，使用 checkpoints 與明確的 pending-cell 清單續跑。不能為配合工具時間而把未完成計算認定成科學失敗。

## 後續回傳

`RETURN_CHECKLIST.md` 列出整合論文所需的資料。僅有最終圖像不足以可靠地修改數值敘述、scope 與 reproducibility。

`SOURCE_BASIS.md` 分別標記稿件既有內容、公開資料來源及本輪提出的新設計。
