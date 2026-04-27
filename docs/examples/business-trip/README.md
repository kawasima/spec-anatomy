# 出張申請サンプル

出張申請システムの完全な Spec Set サンプルです。初期モデルと、洗練後の最終形の2段階で示します。

## このサンプルが扱う業務

出張申請システムの業務ルールは次のとおりです。

- 出張予定費用が10万円以上、または出張申請者が役職なしの場合は、上長の事前承認が必要
- 出張費用負担を先方が持ってくれる場合は、費用負担区分を「先方」に設定する。この場合、金額および出張者の役職に関わらず事前承認が必要
- 出張申請を提出した時点で、事前承認が必要かどうかを判定し、必要ならば上長に事前承認を依頼する
- 出張後に上長がその内容および金額を最終承認し、立て替えた金額を経理に連携する

## 構成

- [spec-model/](spec-model/) — Core の仕様モデル（最終形と初期モデル）
  - [business-trip.md](spec-model/business-trip.md) — 出張申請の data と behavior（洗練後の最終形）
  - [business-trip-initial.md](spec-model/business-trip-initial.md) — 初期モデル（洗練前との比較用）
- [shell/](shell/) — Shell の例（API、永続、UI の最小例）
  - [api/](shell/api/) — REST API の例
  - [persistence/](shell/persistence/) — 永続モデルの例
  - [ui/](shell/ui/) — 画面の例
- [ai-collaboration/](ai-collaboration/) — エージェントとのやり取りのサンプル
  - [refactoring-prompt.md](ai-collaboration/refactoring-prompt.md) — 既存設計書から Core を抽出する例
  - [core-generation-prompt.md](ai-collaboration/core-generation-prompt.md) — Core からコードを生成する例

## 使い方

1. [spec-model/business-trip.md](spec-model/business-trip.md) を読み、最終形の仕様モデルがどう書かれているかを確認します
2. [spec-model/business-trip-initial.md](spec-model/business-trip-initial.md) と比較し、SMDD の洗練（凝集度・結合度・全域性・イミュータブルデータモデル）でどう変わったかを確認します
3. [shell/](shell/) を読み、Core から Shell（API・永続・UI）への変換が「派生元参照」を必須化していることを確認します
4. [ai-collaboration/](ai-collaboration/) のサンプルプロンプトを実プロジェクトの参考にします

## このサンプルが扱う SMDD の観点

- 仕様DSL（data + behavior）の書き方
- 段階的改善（凝集度・結合度・全域性・スタンプ結合排除）
- 状態を OR で分ける（仕様隠しの回避）
- イミュータブルデータモデル（リソース／イベント分類）
- Core/Shell の二段階生成（Core サンプル + Shell の API・永続・UI 例）
- AI Collaboration（refactoring 用と code generation 用のプロンプト）

仕様変更への対処（費目別の拡張、精算手段の拡張）は本サンプルでは省略します。
