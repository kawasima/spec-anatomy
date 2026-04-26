# SIer向け Spec Set

Traditional SIerが扱ってきた網羅的な設計ドキュメント群を、生成AI時代の開発で使える「仕様駆動開発の Spec Set」として組み直したものです。

## このSpec Setが置く中心

仕様モデル（仕様DSL：`data` と `behavior`）を Spec Set の中心に置きます。それ以外（API、永続モデル、画面・帳票・メール、メッセージング契約など）は、すべて仕様モデルから派生する Shell として位置づけます。

この設計判断は、書籍 *Specification Model-Driven Design* の8.3節（インサイドアウト開発）と8.3.2節（Core/Shell の二段階生成）に従っています。Traditional SIerの設計書がしばしば置いてきた「画面駆動」「テーブル駆動」「配線プログラミング」を、仕様駆動の名のもとに高速に再生産しないための構造です。

## 構成

```
docs/spec-set/
├── README.md            この文書
├── design.md            設計方針の詳細
├── spec-model/          Core：仕様DSL の書き方
│   ├── README.md
│   ├── ubiquitous-language.md
│   ├── data/            data 定義の書き方
│   ├── behavior/        behavior 定義の書き方
│   └── workflow/        workflow（複数 behavior の連結）の書き方
├── spec-tests/          仕様テストの規約（書籍5章準拠）
│   ├── README.md
│   ├── invariants/      data の不変条件テスト
│   ├── totality/        behavior の全域性テスト
│   └── state-transitions/ 状態遷移と時系列のテスト
├── shell/               Shell：実装モデルへの変換規約（書籍6章準拠）
│   ├── README.md
│   ├── api/             API 契約への変換規約
│   ├── persistence/     永続モデルへの変換規約
│   ├── ui/              画面・帳票・メールへの変換規約
│   └── messaging/       メッセージング契約への変換規約
├── ai-collaboration/    コーディングエージェントとの協業規約
│   ├── README.md
│   ├── refactoring-with-agents.md  仕様モデル洗練の設計サポート
│   ├── core-generation.md          Core からのコード生成（Strict Spec）
│   ├── shell-generation.md         Shell の生成（Policy & Discretion）
│   └── verification-loop.md        型・テスト・lint による検証ループ
├── adrs/                ADR（実装方針の記録）
│   └── README.md
└── examples/business-trip/  出張申請の完全サンプル
    ├── README.md
    ├── spec-model/      Core の例
    ├── shell/           Shell の例（API、永続、画面の最小例）
    └── ai-collaboration/ エージェントとのやり取りのサンプルプロンプト
```

## Core と Shell の関係

- **Core（spec-model/）** は仕様DSL で書かれます。フレームワーク、DB、UIライブラリへの依存を一切持ちません。エージェントへの入力（書籍8.6 の Strict Spec）として、業務ルールを曖昧さなく伝えます。
- **Shell（shell/）** は仕様モデルから派生する API・永続・UI・メッセージングの規約を書きます。Core を参照しますが、Core は Shell を知りません。一方向の依存です。

依存方向は Shell → Core で固定します。Core を変更したら Shell は影響を受けますが、Shell の都合（フレームワークの制約、テーブル設計の都合、画面項目の差異）が Core に逆流することはありません。

## SIer 現場での始め方

書籍8.3はゼロから Core を書き始める前提ですが、SIer の現場では既存設計書（画面・テーブル・帳票）が先にあるケースが大半です。このSpec Setはその経路にも対応します。

既存設計書を素材に、コーディングエージェントを設計サポートとして使い、段階的に Core を抽出していく経路を [ai-collaboration/refactoring-with-agents.md](ai-collaboration/refactoring-with-agents.md) で扱います。「外側が先に決まる」ことと「インサイドアウトで進める」ことは両立します。

## 何を含めて何を含めないか

判断基準は「**コーディングエージェントに伝えないと実装できないか**」の一点だけです。

含めるもの：

- 業務ルール（事前承認の判定、精算額の計算、状態遷移）
- 業務不変条件（注文金額 = 明細合計 + 税、キャンセル済み注文は再開できない）
- 業務概念モデル（集約境界・状態・ライフサイクル・ドメインイベント）
- ユビキタス言語（用語の業務的意味、近接概念との違い）
- API 契約、画面・帳票・メールの項目（Core からの派生として）
- 永続モデル（テーブル定義、項目バリデーション）
- アーキテクチャ決定（ADR）
- 受け入れ基準・property-based testの性質

含めないもの：

- 採番ユーティリティのようにライブラリ任せになる実装詳細
- テストの実施情報・確認情報（CI履歴で十分）
- 表紙・目次・変更履歴（Gitで十分）
- コードと冗長な処理詳細・編集仕様・物理項目名（書籍8.1.1のテーブル駆動・配線プログラミング由来の項目）

## 進め方

1. [design.md](design.md) で設計方針の全体像を読みます
2. [spec-model/README.md](spec-model/README.md) で仕様DSL の書き方を読みます
3. [examples/business-trip/](examples/business-trip/) で具体例を確認します
4. [ai-collaboration/](ai-collaboration/) でエージェントとの協業の仕方を読みます
5. 自プロジェクトで [spec-model/](spec-model/) 配下に仕様モデルを書き始めます

## 参照する書籍と外部資料

- 書籍 *Specification Model-Driven Design*（仕様モデル駆動設計）
- Scott Wlaschin "Designing with types" シリーズ <https://fsharpforfunandprofit.com/series/designing-with-types/>
- Scott Wlaschin *Domain Modeling Made Functional*（Pragmatic Bookshelf, 2018）
