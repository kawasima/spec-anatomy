# classic

伝統的な設計書ベースの開発と、仕様駆動開発（Spec-Driven Development／Living Documentation）の**ギャップを分析**し、現状の仕様駆動開発においても曖昧なまま使われている「**仕様**」という言葉を**明確に定義**することを目的とする。

## 動機

「仕様駆動開発」は、生成AI時代の開発スタイルとして注目を集めている一方で、「仕様とは具体的に何を指すのか」が論者・文脈・ツールごとに異なり、共通認識が存在しない。
この問題は、たとえばCodeZine [仕様駆動開発への期待と誤解 ～「仕様」とは、結局何なのか～（渡邉洋平, 2026/04）](https://codezine.jp/article/detail/23908) でも *"仕様駆動開発という用語は広く受け入れられつつあるが、言葉が指す範囲の広さゆえに、思い描く前提が人によって異なる"* と指摘されている。具体的には、仕様駆動開発を語る各論で「仕様」が指すものは大きく以下のように分かれる：

- **OpenAPI仕様書を仕様駆動の中心と置く論**
  [Specmatic — Contract-Driven / Specification-Driven Development](https://specmatic.io/) — *"The API specification is always the source of truth for the API"* として、OpenAPI／AsyncAPI仕様書を実行可能なコントラクトに変えることを仕様駆動と位置付ける。
- **BDDシナリオ（Specification by Example）を仕様駆動の中心と置く論**
  [Gojko Adzic — Specifying with Examples (2008)](https://gojko.net/2008/11/04/specifying-with-examples/) — Specification by Example の提唱記事。実行可能な例（シナリオ）こそが仕様であり開発を駆動する、という立場。
- **ドメインモデル（業務概念モデル）を仕様駆動の中心と置く論**
  [Scott Wlaschin — Domain Modeling Made Functional (Pragmatic Bookshelf)](https://pragprog.com/titles/swdddf/domain-modeling-made-functional/) — 関数型の型システムでドメインモデル自体を実行可能な仕様として記述し、それが開発を駆動するとする立場。
- **ADR／意図の記録を仕様駆動の中心と置く論**
  [Joel Parker Henderson — Architecture Decision Record (ADR) collection](https://github.com/joelparkerhenderson/architecture-decision-record) — *"An ADR captures an important architectural decision made along with its context and consequences"* として、設計判断と文脈の連鎖そのものを開発を駆動する仕様とみなす立場。
- **AIエージェントへのスーパープロンプトを仕様駆動の中心と置く論**
  [GitHub — Spec Kit / Spec-Driven Development](https://github.com/github/spec-kit) — *"living, executable artifacts that evolve with the project"* としての仕様。AIエージェントを駆動する版管理されたMarkdown仕様を中心に据える立場。
  [Kiro — Introducing Kiro](https://kiro.dev/blog/introducing-kiro/) — Kiro specsをAIエージェントへの実装ガイドとして扱うAWSの立場。

一方、伝統的な日本のSI／エンタープライズ開発における「設計書」は、
**極めて網羅的で構造化された仕様ドキュメント群**として確立されています。
Nablarch開発標準の「030_設計ドキュメント」はその代表例で、
35種類のExcel／Wordフォーマットからなる体系的な設計書セットを定義しています。

両者は表面的には**「ともに仕様を書く営み」**として括られがちですが、
実際にはカバー範囲・情報の流れの向き・正本の場所・想定読者がまったく異なります。

このリポジトリでは、両者を**同じスキーマの上に並べて比較する**ことで、
仕様駆動開発が想定する「仕様」と伝統的設計書が記述する「仕様」のギャップを構造的に明らかにし、
**「仕様」という語を解像度高く定義し直す**ことを試みます。

## 対象

- 旧来型側：Nablarch開発標準「030_設計ドキュメント」
  https://github.com/nablarch-development-standards/nablarch-development-standards/tree/main/030_設計ドキュメント
  35フォーマット＋36サンプル＋設計書一覧（体系図／実装対応）
- 仕様駆動側：`sdd.md` に記述したLiving Documentation／Spec-Driven Developmentの世界観
  Cyrille Martraire『Living Documentation』をベースに、
  Spec Kit／Kiro系の議論、Birgitta Böckelerの Harness Engineering、
  Spec-first／Spec-anchored／Spec-as-source の3段階整理を踏まえる
