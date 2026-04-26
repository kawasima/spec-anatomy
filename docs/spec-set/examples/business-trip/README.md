# 出張申請サンプル

出張申請システムの完全な Spec Set サンプルです。書籍7.1節の初期モデルと8.5.7節の最終形を題材にしています。

## このサンプルが扱う業務

出張申請システムの業務ルールは次のとおりです。

- 出張予定費用が10万円以上、または出張申請者が役職なしの場合は、上長の事前承認が必要
- 出張費用負担を先方が持ってくれる場合は、費用負担区分を「先方」に設定する。この場合、金額および出張者の役職に関わらず事前承認が必要
- 出張申請を提出した時点で、事前承認が必要かどうかを判定し、必要ならば上長に事前承認を依頼する
- 出張後に上長がその内容および金額を最終承認し、立て替えた金額を経理に連携する

## 構成

- [spec-model/](spec-model/) — Core の仕様モデル（書籍7.1節と8.5.7節の最終形）
  - [business-trip.md](spec-model/business-trip.md) — 出張申請の data と behavior（最終形）
  - [business-trip-initial.md](spec-model/business-trip-initial.md) — 書籍7.1節の初期モデル（拡張前との比較用）
- [shell/](shell/) — Shell の例（API、永続、UI の最小例）
  - [api/](shell/api/) — REST API の例
  - [persistence/](shell/persistence/) — 永続モデルの例
  - [ui/](shell/ui/) — 画面の例
- [ai-collaboration/](ai-collaboration/) — エージェントとのやり取りのサンプル
  - [refactoring-prompt.md](ai-collaboration/refactoring-prompt.md) — 既存設計書から Core を抽出する例
  - [core-generation-prompt.md](ai-collaboration/core-generation-prompt.md) — Core からコードを生成する例

## 使い方

1. [spec-model/business-trip.md](spec-model/business-trip.md) を読み、最終形の仕様モデルがどう書かれているかを確認します
2. [spec-model/business-trip-initial.md](spec-model/business-trip-initial.md) と比較し、書籍3章・4章の洗練でどう変わったかを確認します
3. [shell/](shell/) を読み、Core から Shell（API・永続・UI）への変換が「派生元参照」を必須化していることを確認します
4. [ai-collaboration/](ai-collaboration/) のサンプルプロンプトを実プロジェクトの参考にします

## 書籍との対応

- 1章: 出張申請の業務ルール
- 2章: 仕様DSL の書き方
- 3.5節: 段階的改善の6イテレーション
- 4章: イミュータブルデータモデル（このサンプルでは最終形に直接適用）
- 7.1節: 初期モデル（business-trip-initial.md）
- 7.2節・7.3節: 仕様変更（費目別の拡張、精算手段の拡張）── このサンプルでは省略
- 8.5.7節: 最終形（business-trip.md）
