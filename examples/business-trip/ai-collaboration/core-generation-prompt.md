---
name: Core 生成プロンプト（出張申請）
description: 出張申請の仕様モデル（Core）から TypeScript 実装を生成する Strict Spec プロンプト
status: approved
last-reviewed: 2026-04-28
---

# Core 生成プロンプト（出張申請）

[../spec-model/business-trip.md](../spec-model/business-trip.md) の仕様モデルからエージェントに **Core の TypeScript 実装** を生成させる完成形プロンプトです。Strict Spec の流儀に従い、本質的複雑さを曖昧さゼロで渡します。

規約は [../../reference/spec-set/ai-collaboration/core-generation.md](../../reference/spec-set/ai-collaboration/core-generation.md) を参照。

## このプロンプトを使う場面

- ゼロから Core 実装を生成したい
- 仕様モデルを refactoring したので Core を再生成したい
- 既存の Core 実装を別言語に置き換えたい（プロンプト末尾の言語指定を変える）

## プロンプト本体

````text
あなたは仕様モデル駆動設計（SMDD）に従う Core の実装エージェントです。
次の仕様モデルから TypeScript の Core 実装を生成してください。

## 仕様モデル

[ここに docs/spec-model/business-trip.md の内容を全文貼り付け]

例:

```text
data 社員 = 社員番号 AND 氏名 AND 役職
data 役職 = 管理職 OR 一般社員
data 出張申請 = 出張申請ドラフト OR 申請済み出張申請
data 申請済み出張申請 = 出張予定 AND 申請者 AND 申請日時
data 事前承認必要な出張申請 = 申請済み出張申請 AND 事前承認要件
data 事前承認要件 = 高額出張 OR 役職なし申請 OR 先方負担申請

behavior 事前承認が必要か判断する =
  申請済み出張申請 -> 事前承認必要な出張申請 OR 事前承認不要な出張申請
// 判定ロジック:
// - 出張予定費用合計 >= 100,000 円 → 高額出張
//   Why: 高額支出は組織として事前に妥当性を確認する必要がある
// ...
```

## 制約（Strict Spec）

- 標準ライブラリのみ使用
- フレームワーク（Express、NestJS等）・データベースアクセス・UI ライブラリは一切使わない
- 外部依存（API 呼び出し、DB アクセス、メール送信）は引数として注入する形にする
- 副作用を持つ関数は明示的にマークする
- 例外を投げない。失敗ケースは出力型の OR の一枝として表現する

## 実装方針（Policy）

- TypeScript の strict モード（`exactOptionalPropertyTypes`、`noImplicitReturns`、`noUncheckedIndexedAccess`）
- **判別共用体（tagged union）** で OR を表現。各バリアントには `kind` プロパティ
- **record 型 + readonly** で AND を表現
- Optional は省略可能なフィールドとして表現
- リストは `readonly T[]` または `{ first: T; rest: readonly T[] }`（1件以上を型で保証する場合）
- 識別子は文字列リテラル型ではなくブランド型（`type 社員番号 = string & { __brand: '社員番号' }`）を検討

## 重要な変換規則

| 仕様DSL | TypeScript |
|---|---|
| `data X = A OR B OR C` | `type X = A \| B \| C` （各バリアントに `kind`） |
| `data X = A AND B` | `type X = { readonly a: A; readonly b: B }` |
| `data X = A?` | `type X = { readonly a?: A }` |
| `data X = List<A>` | `type X = readonly A[]` |
| `data X = List<A>` 1件以上 | `type X = { readonly first: A; readonly rest: readonly A[] }` |
| `behavior f = X -> Y` | `function f(x: X): Y` |
| `behavior f = X -> Y OR Z` | `function f(x: X): Y \| Z` |
| `behavior f = X AND Y -> Z` | `function f(args: { x: X; y: Y }): Z`（名前付き引数オブジェクト） |

## 重要な業務概念の保持

仕様モデルで型として刻まれた業務概念を、コード生成時に boolean や enum に「平坦化」しないこと。

- ❌ 悪い例: `if (申請.予定費用合計 >= 100000 || 申請.申請者.役職 === 'なし') { ... }`
- ✓ 良い例:
  ```typescript
  type 事前承認要件 =
    | { kind: '高額出張'; 予定費用合計: number }
    | { kind: '役職なし申請' }
    | { kind: '先方負担申請' };
  ```

理由: 業務的な「なぜ事前承認が必要か」を型として残すことで、後で UI に表示したり、別の判定で再利用できる。

## 状態は型で分けること

状態を表す `kind` で1つの型を分岐させるのではなく、**状態ごとに別の型** に分ける：

- ❌ `type 出張申請 = { id: string; status: 'draft' | 'submitted' | 'approved'; approver?: 社員 }`
- ✓ `type 出張申請ドラフト = { kind: 'ドラフト'; ... }`
  + `type 申請済み出張申請 = { kind: '申請済み'; ...; 申請日時: Date }`
  + `type 出張申請 = 出張申請ドラフト | 申請済み出張申請`

理由: 状態に応じて必須となる項目を型レベルで保証できる。`申請済み出張申請` は申請日時を必ず持つ。

## behavior の入力型は厳密に絞る

`behavior 上長が事前承認する` の入力型は `事前承認必要な出張申請` のみ。`申請済み出張申請` を受け取る形にすると、事前承認不要な申請でも呼べてしまう。

- ❌ `function 上長が事前承認する(申請: 申請済み出張申請, ...): 結果`
- ✓ `function 上長が事前承認する(申請: 事前承認必要な出張申請, ...): 結果`

これにより「ありえない遷移」が型レベルで防がれる。

## 成果物

次のファイル群を出力してください。各ファイルの先頭に「対応する仕様モデルへのリンク」をコメントで記載：

1. **`business-trip-types.ts`** — `data` 定義に対応する型のみ。pure（関数なし）
2. **`business-trip-core.ts`** — `behavior` 定義に対応する pure 関数
3. **`business-trip-ports.ts`** — 副作用を持つ依存（Repository, Clock, Notification など）の interface のみ。実装はしない

各ファイルは **依存関係が一方向** であること: `core.ts` は `types.ts` のみに依存。`core.ts` は `ports.ts` を import しても、副作用関数を呼ばない（呼ぶのは Shell の責務）。

## 出力形式

ファイルごとにコードブロックで出力。冒頭に短い設計意図のコメントを置く。
冗長な docstring は書かない（型と命名で表現する）。
````

## 検証ループとの組み合わせ

エージェントが生成したコードに対して：

1. **型検査**（TypeScript なら `tsc --noEmit`） — 型エラーがないか
2. **lint** — 規約違反がないか
3. **仕様テスト** — 仕様モデルから導かれる性質を検証する（具体ツールは仕様モデルパーサ specifico との統合で扱う予定）
4. **失敗があれば** [verification-loop の規約](../../reference/spec-set/ai-collaboration/verification-loop.md) でエージェントに修正させる

## Strict Spec が機能する条件

このプロンプトが機能するのは、仕様モデル側で次が満たされているとき：

1. 状態ごとに data が OR で分かれている
2. behavior の入力型が業務状態として絞られている
3. Why が各判定規則に書かれている
4. 業務概念が型として刻まれている（boolean ではない）

仕様モデルが上記を満たさない場合は、Core 生成より前に [refactoring-prompt.md](refactoring-prompt.md) で仕様モデル自体を refactoring してください。

## 参照

- [../../reference/spec-set/ai-collaboration/core-generation.md](../../reference/spec-set/ai-collaboration/core-generation.md)
- Scott Wlaschin "Designing with types" シリーズ
- Scott Wlaschin *Domain Modeling Made Functional*
