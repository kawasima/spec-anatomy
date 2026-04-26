# AI Collaboration: コーディングエージェントとの協業規約

このSpec Setは、コーディングエージェントを「実装の生成だけ」ではなく「設計サポート」「検証ループ」も含めて活用する設計プロセスを採ります。

SMDD ではエージェントを Core からのコード生成に使うことが中心ですが、SIer の現場では一段手前 ──仕様モデルそのものの洗練── にもエージェントが活用できます。このディレクトリはその規約を置きます。

## 4つの場面

| 場面                  | 文書                                            | 概要                                                              |
| --------------------- | ----------------------------------------------- | ----------------------------------------------------------------- |
| 仕様モデルの洗練      | [refactoring-with-agents.md](refactoring-with-agents.md) | 既存設計書から Core を抽出、deeper insight への refactoring の駆動 |
| Core からのコード生成 | [core-generation.md](core-generation.md)        | Strict Spec として仕様DSL を渡してコード生成                       |
| Shell の生成          | [shell-generation.md](shell-generation.md)      | Policy & Discretion で API・永続・UI を生成                        |
| 検証ループ            | [verification-loop.md](verification-loop.md)    | 型・テスト・lint・契約テストで生成物を検証                         |

## 全体像

```text
[既存設計書（画面・テーブル・処理詳細）]
          ↓
   refactoring-with-agents.md
          ↓
   仕様モデル（Core）
          ↓
   core-generation.md         shell-generation.md
          ↓                          ↓
   Core の実装コード         Shell の実装コード
          ↓                          ↓
              verification-loop.md
                       ↓
                   本番デプロイ
```

エージェントは各場面で異なる役割を持ちます。

- **設計サポート**：仕様モデル洗練のための提案者
- **コード生成**：仕様モデルからの実装変換者
- **検証**：型・テスト・lint・契約テストの実行者

## エージェントを使う原則

### 1. Core は Strict Spec

業務ルール（本質的複雑さ）はエージェントに「補完」させてはいけません。仕様DSL として曖昧さゼロで渡します（Strict Spec）。

### 2. Shell は Policy & Discretion

実装技術（偶有的複雑さ）はエージェントの裁量を活かします。詳細な手順ではなく、方針（言語、フレームワーク、コーディング規約）を与えます（Policy & Discretion）。

### 3. Why をプロンプトに含める

判定規則の理由をエージェントに渡すと、生成されるコードが条件式の羅列ではなく業務概念の型として表現されます。

### 4. 検証ループを必ず通す

エージェントの生成は決定的ではありません。`temperature=0` でも完全な決定性は保証されません。型検査・テスト・lint・契約テストで毎回検証します。

### 5. 設計サポートとしての利用

仕様モデル洗練そのものにエージェントを使えます。Wlaschin 流の deeper insight への refactoring（"Discovering new concepts" の例）をエージェントが提案し、人間が確定する形のループは、Spec Set の運用規約として明示する価値があります。

## 利用シーンと参照先

### 新規プロジェクトでゼロから書く

SMDD のインサイドアウト開発で進めます。`refactoring-with-agents.md` の「ゼロからの仕様モデル作成」を参照します。

### 既存設計書から Core を抽出する

SIer 現場で多いパターンです。画面・テーブル・処理詳細を素材に、エージェントに仕様モデルへの抽出を依頼します。`refactoring-with-agents.md` の「既存設計書からの抽出」を参照します。

### 仕様モデルから実装コードを生成する

Core を Strict Spec としてエージェントに渡し、Phase 1（Core の実装）と Phase 2（Shell の実装）を分けて生成します。`core-generation.md` と `shell-generation.md` を参照します。

### 仕様モデルを変更したときに実装を追従させる

仕様モデルの差分から影響範囲を特定し、Expand and Contract で段階的に変更を適用します。`verification-loop.md` を参照します。
