# ADR（Architecture Decision Record）

実装方針の判断を記録する場所です。書籍6章の永続モデル選定や、Spec Set の運用判断、Shell 側の技術選定などを ADR として残します。

## ADR が扱う範囲

このSpec Setの ADR は、Spec Set の運用判断と、Shell 側の実装方針の判断に使います。Core（仕様モデル）の業務ルールは ADR ではなく仕様モデル自体に書きます。

ADR の例:

- 永続モデル選定（Data Mapper / Repository / Active Record / CQRS / Event Sourcing）
- 関連の永続化パターン選定（純粋ドメインモデル / ORM 前提 / 交差エンティティ）
- API スタイル選定（REST / GraphQL / gRPC）
- メッセージングブローカー選定（Kafka / RabbitMQ / SQS）
- 認証方式選定（JWT / OAuth / mTLS）
- フレームワーク選定
- 仕様モデル変更時の Expand and Contract 適用判断

## ADR の書き方

書籍6章のテンプレートを参考に、次の構成で書きます。

```markdown
# ADR-XXX <決定の名前>

## ステータス
proposed / accepted / superseded by [ADR-YYY] / deprecated

## 文脈
なぜこの決定が必要になったか、何が問題だったか、どんな選択肢があったか。

## 検討した選択肢

### 選択肢A: <名前>
- 利点
- 欠点

### 選択肢B: <名前>
- 利点
- 欠点

## 決定
どの選択肢を選んだか、なぜか。

## 実装への含意
エージェントがコードを書くときに守るべき具体的な制約。
ArchUnit や lint で強制できる粒度で書く。

## 検証方法
- ArchUnit ルール
- lint ルール
- 契約テスト

## 影響する範囲
- Core: <該当する data / behavior>
- Shell: <該当する API / 永続 / UI / メッセージング>

## 結果
（運用後に振り返りを書き足す）

## 改訂履歴
| 日付       | 変更内容           |
| ---------- | ------------------ |
| YYYY-MM-DD | 初版作成（accepted）|
```

## ファイル名規約

`ADR-{連番3桁}-{kebab-case-name}.md` の形式。

- `ADR-001-data-mapper-pattern.md`
- `ADR-002-jwt-authentication.md`
- `ADR-003-event-sourcing-for-orders.md`

## ADR の依存関係

ADR は Core の `data` や `behavior` を参照することがあります。Core の変更が ADR に影響する場合は、ADR の「影響する範囲」セクションで明示します。

逆に、ADR が Core の設計に影響することもあります（例: 「Event Sourcing を採用するため、Core でドメインイベントを `data` として持つ」）。この場合は、ADR を Core より先に決め、Core の設計に反映します。

## 実装への含意

ADR の中心は「実装への含意」セクションです。書籍8章の流儀に従い、エージェントに守らせる制約を具体的に書きます。

```markdown
## 実装への含意
- payment パッケージから external.gateway パッケージへ直接依存しない
  → 必ず PaymentCommandQueue を経由する
- ArchUnit ルール: src/test/.../PaymentDependencyTest.kt
- 違反検出時は ADR-005 へのリンクをエラーメッセージに含める
```

`payment.isActivated` のような実装詳細を露出する設計は避け、業務上意味のある振る舞いを公開する制約を残します。書籍6.1.3 の Always-valid ドメインモデルとも整合します。

## ADR と仕様モデルの関係

仕様モデルが「業務として何が正しいか（What/Why）」を扱うのに対し、ADR は「業務上の正しさを保つために、実装でどう制約をかけるか（How）」を扱います。両者は補完的です。

- 仕様モデル: 注文承認には承認者が必須である（業務ルール）
- ADR: 永続モデルとドメインモデルを分離する Data Mapper パターンを採用する（実装方針）

ADR は仕様モデルから派生する技術判断なので、仕様モデルが変わっても ADR がそのまま有効なことが多いです。逆に ADR が変わっても仕様モデルは変わりません（業務ルールは技術選定に依存しない）。

## サンプル

実プロジェクトでの最初の ADR として、永続モデル選定（ADR-001）と認証方式選定（ADR-002）を書くと、後続の ADR の書き方の指針になります。サンプルは [../examples/business-trip/](../examples/business-trip/) を参照。

## 参照

- 書籍6章（実装モデルの分離、ADR で永続モデル選定を記録）、8章（実装への含意の書き方）
- Joel Parker Henderson "Architecture Decision Records" コレクション <https://github.com/joelparkerhenderson/architecture-decision-record>
- Archgate（実行可能 ADR）<https://archgate.dev/>
