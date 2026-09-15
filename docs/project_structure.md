# Project structure and data flow

Repository 採用「workstream 垂直切分、核心能力水平共用」的結構。

```text
                         python run.py
                              |
                  +-----------+-----------+
                  |                       |
              P0 router               P1 router
                  |                       |
          workstream config       workstream config
                  |                       |
          P0 simulation           P1 matched simulation
                  \                       /
                   +------ shared core --+
                              |
                    isolated artifacts
```

`src/stationary_bias/core/` 只放跨 workstream 的穩定元件：objective/noise model、
SCAFFOLD kernel、統計推論、驗證、共用理論、I/O 與繪圖樣式。它不決定特定研究題目
的矩陣、停止規則或輸出報告。

`src/stationary_bias/workstreams/<slug>/` 擁有該題目的 simulation、analysis、theory
補充與 figures。對應的設定、說明與 artifacts 放在 repository 根目錄下同名的
`workstreams/<slug>/`，因此從資料夾名稱即可一路找到入口與輸出。

## Artifact isolation

```text
workstreams/p0_scaffold_bias/artifacts/
  publication_snapshot/      原始出版研究快照
  small_step_confirmation/    P0 小步長確認
  smoke/                      可拋棄的快速檢查

workstreams/p1_matched_fedavg/artifacts/
  smoke/                      P1 快速檢查
  formal/<matrix-id>/         P1 正式矩陣快照
  archive/                    命名整理前保存的出版快照
```

P1 formal runner 只接受乾淨且已有 commit 的來源。它先在 canonical 目錄旁的 staging
目錄建立 raw CSV、run-start provenance、摘要、manifest、報告與圖片；全部產生後，
才檢查既有 canonical raw CSV 的科學欄位是否完全相同。相同時整體交換目錄，不同時
保留原目錄。交換失敗時會復原原目錄。`archive/` 永遠不會成為交換目標。

Smoke 路徑由 `.gitignore` 排除並可直接覆寫。衍生摘要、報告與圖片可從已保存的 raw
CSV 重建。run-start provenance 在 staging 目錄建立前取得，因此實驗輸出不會改變
所記錄的來源 dirty state。

## Adding a workstream

1. 在 `workstreams/ROADMAP.md` 登錄研究問題、方法與範圍。
2. 建立 `workstreams/<pN_slug>/{README.md,study.yaml,configs/,artifacts/}`。
3. 實作放 `src/stationary_bias/workstreams/<pN_slug>/`，測試鏡像放
   `tests/workstreams/<pN_slug>/`。
4. 只有真正跨題目且介面穩定的元件才上移至 `core/`。
5. 在 `src/stationary_bias/cli.py` 註冊 `python run.py pN ...` 入口。

## Documentation contract

Repository 內的說明文件只描述目前可由程式、設定或 artifact 驗證的專案內容，包括
研究問題、方法、入口、資料結構、輸出規格與科學判定。專案管理進度、空的 workstream
佔位、工作清單及撰寫工具不屬於公開研究文件；這些資訊使用版本控制歷史或外部 issue
tracker 管理。
