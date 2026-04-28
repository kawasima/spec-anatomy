# Shell の生成（Policy & Discretion）

仕様モデル（Core）から派生する Shell（API、永続、UI、メッセージング）をエージェントに生成させる規約です。Policy & Discretion の流儀に従います。

## 原則：偶有的複雑さには裁量を残し方針を与える

実装技術（フレームワーク、ORM、テンプレートエンジン、UIライブラリ）は偶有的複雑さです。これらに対しては、エージェントの知識と推論能力を活かして最適な実装パターンを選ばせます。詳細な手順ではなく、方針を与えます。

## 悪いプロンプトと良いプロンプト

### 悪いプロンプト

```text
checkApproval 関数を作成し、引数に amount を取り、
if 文で 100000 と比較して、true を返す関数を作ってください。
```

このマイクロマネジメントは、エージェントの「最適な実装パターンを選択する能力」を阻害します。プロンプト記述コストが実装コストを上回り、経済的にも合理性を欠きます。

### 良いプロンプト

```text
Phase 1 で生成した Core の TypeScript 実装を使って、
REST API のエンドポイントを実装してください。

実装方針:
- フレームワーク: Express
- 認証: JWT
- バリデーション: zod
- エラーハンドリング: Core の Result 型を HTTP ステータスコードにマッピング
- ロギング: pino
- テスト: 契約テストを supertest で書く

制約:
- Core の型は一切変更しない
- Core の関数を呼び出す形でエンドポイントを実装する
- Core にない業務ロジックを Shell に書かない（業務ロジックが必要なら Core に戻る）
```

## Phase 2: Shell の実装

Core/Shell 二段階生成の Phase 2 として、Phase 1 で生成した Core を取り囲む Shell を実装します。

### Shell の役割

- ユーザー入力を Core が理解する型に変換するアダプター
- Core の出力を UI や DB に適した形に変換するアダプター
- 永続化やネットワーク通信のような副作用を扱う

### 各 Shell コンポーネントの方針

#### API（REST、gRPC、GraphQL など）

```text
方針:
- フレームワーク: <選定>
- 認証認可: <選定>
- バリデーション: 境界で Core の型に変換、Core の不変条件は変換時にチェック
- エラーレスポンス: Core の Result 型を HTTP ステータスコードにマッピング
  - 検証エラー → 400
  - 権限エラー → 403
  - 状態不整合エラー → 409
- 機械可読契約: OpenAPI で書き出す

制約:
- Core の関数を直接呼び出す
- Core にない業務ロジックを書かない
```

#### 永続（DB、ORM）

```text
方針:
- DB: <選定>
- マッピング戦略: <Data Mapper / Repository / Active Record>
- マイグレーション: <Flyway / Liquibase / Prisma Migrate>
- トランザクション: behavior 単位で1トランザクション

制約:
- 永続モデルとドメインモデル（Core）を別の型にする
- Mapper で Core の data ⇔ 永続モデルの相互変換
- Core にない型を永続モデルとして発明しない（必要なら Core に戻る）
```

#### UI（Web、モバイル、デスクトップ）

```text
方針:
- フレームワーク: <選定>
- 状態管理: <選定>
- スタイリング: <選定>
- i18n: <選定>

制約:
- Core の data から派生する項目のみ表示する
- 編集仕様（数値の桁区切り、日時のフォーマット）は Shell に閉じる
- ユーザー入力は境界で Core の型に変換する
- Core にない項目を画面側で発明しない（必要なら Core に戻る）
```

#### メッセージング

```text
方針:
- ブローカー: <選定>
- スキーマレジストリ: <選定>
- メッセージ形式: <Avro / Protobuf / JSON>
- 配信保証: <At-most-once / At-least-once / Exactly-once>

制約:
- Core のドメインイベントをペイロードのスキーマとして使う
- 重複検知は messageId で行う
- Core にないイベントを Shell で発行しない
```

## Strict と Discretion の境界

Shell の生成でも、次は Strict として渡します。

- **Core の型を変更しない**（追加・削除・型変更を禁止）
- **Core の関数を呼び出す形で実装**（業務ロジックを Shell に書かない）
- **エラー処理は Core の Result 型に従う**（例外で握りつぶさない）

それ以外（フレームワーク選定、コード構造、ファイル分割、命名規約）はエージェントの裁量に任せます。

| 関心事         | アプローチ              |
| -------------- | ----------------------- |
| 業務ルール     | Strict Spec（厳密）      |
| 型の構造       | Strict Spec（厳密）      |
| エラー処理方針 | Strict Spec（厳密）      |
| フレームワーク | Policy（方針）           |
| ライブラリ選定 | Policy（方針）           |
| コード構造     | Discretion（裁量）       |
| 命名・ファイル | Discretion（裁量）       |

## 検証

生成された Shell を次の観点で確認します。

- Core を呼び出す形で実装されているか
- 業務ロジックが Shell に書かれていないか（書かれていれば Core に戻る）
- Core の型が変更されていないか
- 契約テスト・統合テストで Core と Shell の境界が検証されているか
- Core にない項目／イベント／メソッドが Shell で発明されていないか

詳細は [verification-loop.md](verification-loop.md)。

## 参照

- Martin Fowler *Patterns of Enterprise Application Architecture*（実装モデルのパターン）
