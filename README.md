# Spec Anatomy

SIer向けの仕様駆動開発のSpec Setを設計するリポジトリです。仕様モデル駆動設計（Specification Model-Driven Design, SMDD）の枠組みを下敷きに、Core（仕様モデル）と Shell（実装モデル）の二段階で構成します。

## このリポジトリの目的

「仕様駆動開発」は、生成AI時代の開発スタイルとして注目を集めている一方で、「仕様とは具体的に何を指すのか」が論者・文脈・ツールごとに異なります。CodeZine [仕様駆動開発への期待と誤解 ～「仕様」とは、結局何なのか～（渡邉洋平, 2026/04）](https://codezine.jp/article/detail/23908) も *"仕様駆動開発という用語は広く受け入れられつつあるが、言葉が指す範囲の広さゆえに、思い描く前提が人によって異なる"* と指摘しています。

各論で「仕様」が指すものは大きく分かれています。OpenAPIを中心に置く論（[Specmatic](https://specmatic.io/)）、BDDシナリオを中心に置く論（[Gojko Adzic — Specifying with Examples (2008)](https://gojko.net/2008/11/04/specifying-with-examples/)）、ドメインモデルを中心に置く論（[Scott Wlaschin — Domain Modeling Made Functional](https://pragprog.com/titles/swdddf/domain-modeling-made-functional/)）、ADRを中心に置く論（[Joel Parker Henderson — ADR collection](https://github.com/joelparkerhenderson/architecture-decision-record)）、AIエージェントへのスーパープロンプトを中心に置く論（[GitHub spec-kit](https://github.com/github/spec-kit)、[Kiro](https://kiro.dev/blog/introducing-kiro/)）が並走しています。

一方で、Traditional SIerの世界では網羅的で構造化された設計書群が確立しています。代表例の[Nablarch開発標準の030_設計ドキュメント](https://github.com/nablarch-development-standards/nablarch-development-standards/tree/main/030_設計ドキュメント)は35フォーマットの設計書セットを定義しています。両者は「ともに仕様を書く営み」として括られがちですが、カバー範囲・情報の流れの向き・正本の場所・想定読者は大きく異なります。

このリポジトリは、両者を比較して「仕様」という語を解像度高く定義し直し、その上でSIer向けのSpec Setを設計・サンプル化することを目的にしています。Spec Setの中心に置くのは、書籍 *Specification Model-Driven Design* で定義される **仕様モデル（仕様DSL：data + behavior）** です。Traditional SIerの設計書（画面・テーブル・帳票など）はそこから派生する Shell として位置づけ直します。

## 構成

- [sdd.md](sdd.md): Living Documentation／Spec-Driven Development の世界観の整理（現状分析）
- [sdd-vs-traditional-design-docs.md](sdd-vs-traditional-design-docs.md): Traditional SI設計書と sdd の突き合わせ（現状分析）
- [docs/spec-set/](docs/spec-set/): SIer向け Spec Set の本体
  - [docs/spec-set/spec-model/](docs/spec-set/spec-model/): Core。仕様DSL の書き方
  - [docs/spec-set/spec-tests/](docs/spec-set/spec-tests/): 仕様テストの規約
  - [docs/spec-set/shell/](docs/spec-set/shell/): Shell。API・永続・UI・メッセージングへの変換規約とテンプレート
    - 各カテゴリに `templates/` を持つ（Traditional SI設計書の項目構造を下敷きにした個別・カタログテンプレート）
  - [docs/spec-set/ai-collaboration/](docs/spec-set/ai-collaboration/): コーディングエージェントとの協業規約
  - [docs/spec-set/adrs/](docs/spec-set/adrs/): ADR（実装方針の記録）
  - [docs/spec-set/examples/business-trip/](docs/spec-set/examples/business-trip/): 出張申請の完全サンプル
- [traditional-design-schema.dsl](traditional-design-schema.dsl): Traditional SI 設計書（Nablarch開発標準）の構造化DSL

## Spec Setの判断基準

何を Spec Set に含めるかの判断基準は「**コーディングエージェントに伝えないと実装できないか**」の一点です。エージェントに渡せばエージェントが補える情報、コードや既存ライブラリから推論できる情報、運用記録に置き換えられる情報は、Spec Setに含めません。

詳細は [docs/spec-set/](docs/spec-set/) を参照してください。
