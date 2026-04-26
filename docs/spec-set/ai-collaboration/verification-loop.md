# 検証ループ

エージェントの生成は完全な決定性を持ちません。`temperature=0` でも揺れが残ります。生成のたびに型・テスト・lint・契約テストで検証する規約です。

書籍8.4 の留保（経済性逆転は検証ループが回ることが前提）と書籍5章（仕様テスト）に従います。

## なぜ検証ループが必要か

書籍8.4 で「仕様モデル更新が実装変更の最短経路になる」という経済性逆転が論じられていますが、これは検証ループが回ることが前提です。

エージェントの生成には次のリスクが残ります。

- 生成のたびに微妙な揺れがある（同じプロンプトでも結果が変わる）
- 仕様の意図を外したコード（業務不変条件を破る、状態遷移の網羅性を欠く）
- 学習データのバイアス（古い API 名、推奨されない実装パターン）

これらを人間のレビューだけで防ぐのは困難です。型システム・テスト・lint・契約テストを組み合わせ、決定論的にエラーを検出する仕組みが必要です。

## 検証の4層

### 1層: 型検査

生成された型が、Core の `data` 構造と1対1対応しているかをコンパイラに任せます。

- TypeScript: `tsc --strict`
- Java: javac with `-Werror`
- Rust: rustc

仕様DSL の `OR` が判別共用体になっているか、`AND` がレコード型になっているか、`?` が省略可能フィールドになっているかを、型エラーが出ないことで保証します。

### 2層: 仕様テスト

書籍5章の3軸（構造・変換・時系列）のテストを生成します。

- **構造の正しさ（[../spec-tests/invariants/](../spec-tests/invariants/)）**: data の不変条件を property-based test で検証
- **変換の正しさ（[../spec-tests/totality/](../spec-tests/totality/)）**: behavior の全域性を入力区分ごとに検証
- **時系列の正しさ（[../spec-tests/state-transitions/](../spec-tests/state-transitions/)）**: 状態×操作の組み合わせ表を網羅し、イベント系列の整合を検証

エージェントに「仕様モデルからテストを生成してください」と依頼し、property-based test（Hypothesis、jqwik、QuickCheck）として実装します。

### 3層: 契約テスト

API、永続モデル、メッセージング契約と Core の data の対応を検証します。

- API契約テスト: OpenAPI スキーマと実装のレスポンスが一致するか
- 永続モデルテスト: テーブル定義と Core の data の Mapper が双方向で一致するか
- メッセージングテスト: ペイロードスキーマと Core のドメインイベントが一致するか

### 4層: lint と静的解析

書籍8章で批判されるアンチパターンを lint で検出します。

- 仕様隠し検出（boolean フラグでの状態管理、status 文字列での分岐など）
- スタンプ結合検出（不要に大きい型を受け取る関数）
- Core への外部依存検出（Core から Shell の名前空間を import している）

ArchUnit、ESLint カスタムルール、Architectureテストツール（Archgate など）を使います。

## 仕様モデル lint

このSpec Setの仕様モデル自体にも lint をかけます。

### Front matter スキーマ

各 Markdown ファイルの Front matter が規約に従っているかを検証します。

- 必須項目（name、status、last-reviewed）が揃っているか
- status は `draft` / `approved` / `deprecated` のいずれか
- last-reviewed は ISO 8601 形式の日付

### 仕様DSL の構文チェック

コードブロック内の仕様DSL が文法に従っているかを検証します。

- `data` / `behavior` / `workflow` の文法が正しいか
- 未定義の型を参照していないか
- `OR` の枝に重複がないか

### 命名と用語の整合

`spec-model/ubiquitous-language.md` に登録された用語と、`spec-model/data/` `spec-model/behavior/` で使われている名前が一致しているか。

## 検証ループの運用

### 仕様モデル変更時

仕様モデルを変更したら、エージェントに次を依頼します。

```text
仕様モデルの差分を分析して、影響範囲を特定してください。
- 変更された data を参照している behavior
- 変更された behavior を呼び出している workflow
- 変更された data に対応する API、永続、UI、メッセージング

書籍5.7.1 の3分類（拡張・制約強化・破壊的変更）で評価してください。
```

エージェントが返した影響範囲を確認し、必要な変更を Phase 1（Core）と Phase 2（Shell）で生成し直します。

### Expand and Contract

破壊的変更や制約強化はビッグバンリリースを避けます。書籍8.7.2 の Expand and Contract パターンで段階的に適用します。

```text
Step 1: Expand
仕様モデル: 新しいフィールドを Optional として追加
実装: 新旧両方を扱うコードを追加

Step 2: Migrate
データ移行バッチで既存レコードを埋める
新しいフィールドを使うコードを順次追加

Step 3: Contract
仕様モデル: Optional を必須に変更
実装: 新旧両対応コードを削除
```

エージェントには「過渡期の実装」を明示的に要求します。デフォルトでは最終形を一気に生成しようとするためです。

### CI への組み込み

検証ループは CI で常時回します。

- 仕様モデル lint（Front matter、仕様DSL 構文）
- 型検査（`tsc --strict`、`javac` 等）
- 仕様テスト（property-based test、状態遷移網羅）
- 契約テスト（OpenAPI、永続モデル、メッセージング）
- アーキテクチャテスト（Core/Shell 依存方向、仕様隠し検出）

これらが PR 単位で全て pass することを Spec Set の運用要件にします。

## 失敗時の対処

検証ループでエラーが出たときは、次の順で対処します。

1. **Core の問題か Shell の問題かを切り分ける**: Core の生成エラーなら仕様モデルに戻る。Shell のエラーなら方針プロンプトを調整する
2. **業務ルールの問題か実装の問題かを切り分ける**: 業務ルールの問題なら仕様モデルを修正する。実装の問題ならエージェントに再生成を依頼する
3. **エラーが頻発するなら仕様モデルが洗練不足のサイン**: [refactoring-with-agents.md](refactoring-with-agents.md) の deeper insight への refactoring に戻る

## 参照

- 書籍5章（仕様テスト）、8.4節（経済性逆転とその前提）、8.7節（仕様モデルの変更を安全に届ける）、8.7.2節（Expand and Contract）
