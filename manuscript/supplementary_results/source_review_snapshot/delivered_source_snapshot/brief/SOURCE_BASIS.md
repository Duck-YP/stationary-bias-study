# 來源與新增設計的區分

## 稿件既有內容

本執行規格核對了本對話最新整合專案：

- 檔名：`SCAFFOLD_Coefficient_Comparison_Revised_20261009.zip`
- SHA256：`c5518a244cc3a79b9e6a9bd3a61e0fc9d1164376dc12363af4295453687cc389`
- 直接核對的 source：`sections/03_setting_preliminaries.tex`、`appendix/C_numerical_details.tex`。
- 理論係數、uniformity scope 與更新式也見對話提供的 Main Results / Appendix excerpts。

借用的內容是演算法 recursion、two-dimensional nonlinear objective、noise model、theoretical coefficient formulas 和原 H=4 記錄的證據界線。新 grid、seeds、data experiment、estimation plan 和執行階段均不是原稿已執行的實驗。

## 本輪公開来源核對

於 2026-10-09 核對 LIBSVM 官方 binary-classification dataset page：

- https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary.html
- a9a / Adult：123 features；32,561 training rows；16,281 testing rows。
- training：https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/a9a
- testing：https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/a9a.t

SCAFFOLD 原始研究入口：

- https://proceedings.mlr.press/v119/karimireddy20a.html

實際執行端仍須下載並驗證檔案，保存真實取得日期、SHA256 及 row counts。本任務包沒有夾帶 dataset，也沒有宣稱已下載兩個原始資料檔。

## 本輪提出、尚未執行的設計

- gamma × 1/N factorial experiment 與 fixed-N leading-coefficient test。
- bounded affine objective shifts 下的 control-translation implementation check；exact algebra 可直接核對，但不是完整一般 heterogeneous 二階定理。
- a9a retained 32,512-row dataset、124-parameter regularized logistic model、three partition regimes。
- fixed total batch allocation、gamma/H policy contrasts、bias/variance/task-loss readouts。
- pilot-frozen sampling design、optional zero-mean shadow-process estimator、結果回傳格式。

這些是待執行研究 protocol，不能以本文件作為任何 empirical effect 已成立的證據。
