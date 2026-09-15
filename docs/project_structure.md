# Project structure and data flow

Repository 採用「研究 workstream 垂直切分、穩定能力水平共用」的結構。

```text
                         python run.py
                              |
                    workstream registry
                              |
                     workstream modules
                              |
                         shared core
                              |
                  workstream-owned artifacts
```

`src/stationary_bias/core/` 只放跨 workstream 且介面穩定的能力，例如模型、演算法 kernel、統計推論、驗證、artifact transaction、I/O 與繪圖樣式。
研究矩陣、seeds、停止規則、判定門檻與結果敘事由個別 workstream 擁有。

## Workstream layout

```text
workstreams/<slug>/
  README.md                 研究問題、方法、入口與結果解讀
  study.yaml                workstream policy and metadata
  configs/                  matrices, seeds, thresholds and budgets
  artifacts/
    smoke/                  disposable engineering checks
    formal/<matrix-id>/     canonical formal result
    archive/                optional immutable snapshots

src/stationary_bias/workstreams/<slug>/
  simulation / analysis / theory / figures / routing

tests/workstreams/<slug>/
  contract and regression tests
```

只建立實際需要的檔案與 artifact 類別，不建立空的階段佔位。

## Artifact lifecycle

每個 workstream 只寫入自己的 artifact 目錄。
Formal runner 先在 staging 產生 raw data、provenance、摘要、manifest、報告與圖片，通過 workstream policy 的驗證後才整體替換 canonical directory；失敗時保留原目錄。
`archive/` 不得成為替換目標。

Smoke output 是否忽略或覆寫由 workstream policy 決定。
衍生內容應能從保存的 raw data 重建。

## Adding a workstream

1. 登錄研究問題、方法、範圍與預期證據。
2. 建立 workstream 說明、設定、實作與測試。
3. 凍結 inferential unit、run matrix、seeds、停止規則、gates、provenance policy 與 artifact schema。
4. 只將跨題目且介面穩定的元件移入 `core/`。
5. 註冊 CLI 入口與 repository-level checks。

## Documentation contract

`docs/` 描述共用架構、數值原則與資料生命週期；`workstreams/<slug>/` 描述個別研究。
文件只記錄可由程式、設定或 artifact 驗證的內容。
