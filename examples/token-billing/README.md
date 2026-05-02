---
name: トークン課金サービスサンプル
description: LLM API のトークン使用量から請求額を計算する Spec Set サンプル
status: draft
last-reviewed: 2026-05-02
---

# トークン課金サービス（Token Billing）サンプル

LLM API プラットフォームのトークン使用量から請求額を計算するサービスの Spec Set です。元の素材は [gszhangwei/token-billing](https://github.com/gszhangwei/token-billing) の要件文書とテーブル定義で、これを spec-anatomy の Spec Set 規約に沿って書き起こしたものです。

出張申請サンプル（[../../docs/](../../docs/)）に比べると、ドメインが「トークン消費 → 請求」の単一フローに絞られているため、Spec Set 全体も小ぶりになります。SMDD の6条件の中で特に効くのは、**請求結果を「枠内請求」と「超過込み請求」で OR 分割し、超過レートが必須となる側を型で固定する** ところです。

## 業務の概要

- 顧客は月単位の含み枠（monthly quota）と超過時のレート（overage rate per 1K tokens）を持つ料金プランに加入する
- API 利用ごとに prompt tokens と completion tokens を申告する
- 当月の合計トークン消費量に対して、含み枠を消費した分はゼロ円、含み枠を超過した分のみ `(超過トークン数 / 1000) × 超過レート` で請求する
- 計算結果は請求記録（bill）として保存される

詳細な受け入れ基準は [ai-collaboration/source-material.md](ai-collaboration/source-material.md) に元の要件文書を保存してあります。

## 構成

- [spec-model/](spec-model/) — Core の仕様モデル
  - [token-billing.md](spec-model/token-billing.md) — トークン課金の data と behavior
- [shell/](shell/) — Shell の例
  - [api/token-billing-api.md](shell/api/token-billing-api.md) — REST API 契約
  - [persistence/token-billing-table.md](shell/persistence/token-billing-table.md) — 永続モデル
- [spec-tests/](spec-tests/) — 仕様テスト
  - [totality.md](spec-tests/totality.md) — `請求を計算する` の全域性
  - [invariants.md](spec-tests/invariants.md) — data の不変条件
- [ai-collaboration/](ai-collaboration/) — エージェント協業の素材
  - [source-material.md](ai-collaboration/source-material.md) — 元になった要件文書とテーブル定義
  - [evaluation.md](ai-collaboration/evaluation.md) — 各プロンプトの出力との差分（Phase B で追記予定）

## このサンプルが扱う SMDD の観点

- **状態を OR で分ける**: 請求を `枠内請求 OR 超過込み請求` に分け、超過レートが必須となる側を型で固定する
- **抽象概念を立てる … ではなく**「**超過レート適用条件**」を型として導入する。boolean フラグや null 許容で済ませない
- **全域性**: `請求を計算する` behavior は枠残量と消費量の組合せに対して必ず2つの結果型のいずれかに着地する
- **スタンプ結合排除**: 計算ロジックは「当月実績」「料金プラン」「申告トークン」を引数に取り、顧客集約全体を渡さない
- **Core/Shell 分離**: 月境界・通貨丸め・採番のような技術的詳細は Shell に閉じる

## 出張申請サンプルとの違い

| 観点                     | 出張申請                          | トークン課金                       |
| ------------------------ | --------------------------------- | ---------------------------------- |
| 状態遷移の長さ           | 長い（ドラフト→申請→承認→実績→最終承認） | 短い（提出→計算→記録）            |
| 集約の粒度               | 中（出張申請 + 費用）             | 中（顧客 + サブスク + 請求）       |
| 型分割が効く場所         | 事前承認要件・承認結果            | 枠内請求 vs 超過込み請求           |
| Shell の数               | API + 永続 + UI                   | API + 永続（UIなし、機械間連携）   |

## Phase B の予定

このサンプルは [docs/ai-collaboration/](../../docs/ai-collaboration/) のプロンプト群（core-generation / shell-generation / refactoring）を評価するためのリグレッションテストケースとしても使います。要件文書のみを与えて各プロンプトを実行し、生成物を [ai-collaboration/evaluation.md](ai-collaboration/evaluation.md) で本サンプルと比較する予定です。
