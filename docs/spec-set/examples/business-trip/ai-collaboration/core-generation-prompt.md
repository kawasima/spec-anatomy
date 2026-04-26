---
name: Core からコード生成するサンプルプロンプト
description: 仕様モデル（Core）を Strict Spec として TypeScript に変換する例
status: approved
last-reviewed: 2026-04-25
---

# Core からコード生成するサンプルプロンプト

書籍8.6.1 の Strict Spec に従って、Core の仕様モデルからエージェントに TypeScript コードを生成させる例です。

## Phase 1: Core の実装

```text
書籍 *Specification Model-Driven Design* 8.3.2節の Phase 1 として、
次の仕様モデルを TypeScript で実装してください。

## 仕様モデル

[../spec-model/business-trip.md の data と behavior をすべて貼り付け、
Why コメントも含める]

## 制約（Strict Spec）

- 標準ライブラリのみ使用
- フレームワーク（Express、NestJS等）・データベースアクセス・UIライブラリは
  一切使わない
- 外部依存（API呼び出し、DB アクセス、メール送信）は引数として注入する形にする
- 副作用を持つ関数は明示的にマークする

## 実装方針（Policy）

- TypeScript の strict モード（exactOptionalPropertyTypes、noImplicitReturns 等）
- 判別共用体（tagged union）で OR を表現。各バリアントには `kind` プロパティ
- record 型と readonly で AND を表現
- Optional は省略可能なフィールドとして表現
- エラーは例外ではなく `Result` 型として表現
  - `type Result<T, E> = { kind: 'Ok', value: T } | { kind: 'Err', error: E }`
- 仕様DSL の data 定義は Type alias または record 型として変換
- 仕様DSL の behavior 定義は純粋関数として変換

## 重要な変換規則

1. `data X = A OR B OR C` → `type X = A | B | C`
   - 各バリアントは `kind` プロパティで区別
2. `data X = A AND B` → `type X = { readonly a: A; readonly b: B }`
3. `data X = A?` → `type X = { readonly a?: A }`
4. `data X = List<A>` → `type X = readonly A[]`
5. `behavior f = X -> Y OR Z` → `function f(x: X): Result<Y, Z>`

## 重要な業務ルールの保持

- 「事前承認要件」は型として表現すること（条件式の羅列にしないこと）
  - 期待される実装:
    `type 事前承認要件 = { kind: '高額出張'; amount: number } | { kind: '役職なし' } | { kind: '先方負担' }`
- 状態ごとに別の型に分けること（`PreApproved` と `Submitted` を同じ型にしない）
- behavior の入力型は仕様モデルのとおり厳密に絞ること

## 成果物

- 型定義（data に対応）
- 純粋関数（behavior に対応）
- 副作用を持つ依存関数の型定義（インターフェースのみ）
- 各ファイルに「対応する仕様モデルへのリンク」をコメントで記載
```

## Phase 2: Shell の実装

Phase 1 で生成した Core を呼び出す Shell を生成させます。

```text
書籍8.3.2節の Phase 2 として、Phase 1 で生成した Core の TypeScript 実装を使って、
REST API を実装してください。

## Phase 1 の Core

[Phase 1 で生成された TypeScript コードを貼り付け]

## 実装方針（Policy）

- フレームワーク: Express
- 認証: JWT（bearer token）
- バリデーション: zod
- エラーハンドリング: Core の Result 型を HTTP ステータスコードにマッピング
  - 検証エラー → 400
  - 権限エラー → 403
  - 状態不整合エラー → 409
- ロギング: pino
- テスト: 契約テストを supertest で書く

## 制約

- Core の型は一切変更しない
- Core の関数を呼び出す形でエンドポイントを実装する
- Core にない業務ロジックを Shell に書かない（業務ロジックが必要なら Core に戻る）
- 永続化は OrderRepository のような interface に依存させる

## エンドポイントと behavior の対応

[../shell/api/business-trip-api.md の表をそのまま貼り付け]

## 成果物

- Express ルーター
- リクエストバリデーション（zod スキーマ）
- Core 関数の呼び出しとレスポンスマッピング
- エラーハンドリングミドルウェア
- 契約テスト（supertest）
```

## Phase 3: 検証ループ

書籍5章の3軸（構造・変換・時系列）のテストを生成させます。

```text
[../spec-model/business-trip.md] の仕様モデルから、
書籍5章の規約に従ったテストを TypeScript で生成してください。

## 必要なテスト

1. 構造の正しさ（不変条件）
   - 出張予定費用の合計が 0 以上
   - 出張開始日 <= 出張終了日
   - 申請済み出張申請には申請日時が存在する
   - 事前承認OK には承認者と承認日時が存在する

2. 変換の正しさ（全域性）
   - 「事前承認が必要か判断する」がすべての入力区分に対して結果を返す
   - 「上長が事前承認する」が承認者一致／不一致の両方に対応する

3. 時系列の正しさ（状態遷移）
   - 状態×操作の組み合わせ表を網羅
   - 禁止遷移（出張申請ドラフトに対して上長が事前承認する）が型レベルで防がれる

## 実装方針

- property-based test: fast-check
- 状態遷移テスト: 各状態×操作の表を fast-check で網羅
- 各テストファイルの先頭に対応する仕様モデルのセクションへのリンクをコメント
```

## 出力例

エージェントの出力例（Phase 1）:

```typescript
// 仕様モデル: ../spec-model/business-trip.md
// 出張申請の data と behavior を TypeScript として実装

// === data ===

export type 役職 =
  | { readonly kind: '管理職'; readonly level: number }
  | { readonly kind: '一般社員' };

export type 費用負担区分 = '自社負担' | '先方負担';

export type 社員 = {
  readonly 社員番号: string;
  readonly 氏名: string;
  readonly 役職: 役職;
};

export type 事前承認要件 =
  | { readonly kind: '高額出張'; readonly amount: number }
  | { readonly kind: '役職なし申請' }
  | { readonly kind: '先方負担申請' };

export type 出張申請ドラフト = {
  readonly kind: 'ドラフト';
  readonly 出張予定: 出張予定;
  readonly 申請者: 社員;
};

export type 申請済み出張申請 = {
  readonly kind: '申請済み';
  readonly 出張予定: 出張予定;
  readonly 申請者: 社員;
  readonly 申請日時: Date;
};

export type 事前承認必要な出張申請 = {
  readonly kind: '事前承認必要';
  readonly 申請済み: 申請済み出張申請;
  readonly 事前承認要件: readonly 事前承認要件[];
};

// ... 省略

// === behavior ===

export type Result<T, E> =
  | { readonly kind: 'Ok'; readonly value: T }
  | { readonly kind: 'Err'; readonly error: E };

export function 事前承認が必要か判断する(
  申請: 申請済み出張申請,
): 事前承認必要な出張申請 | 事前承認不要な出張申請 {
  const 要件: 事前承認要件[] = [];

  // 高額出張: 高額支出は組織として事前に妥当性を確認する必要がある
  const 合計 = 申請.出張予定.出張予定費用.reduce((sum, 日程) => sum + 日程.予定金額, 0);
  if (合計 >= 100_000) {
    要件.push({ kind: '高額出張', amount: 合計 });
  }

  // 役職なし申請: 役職なしの社員は支出判断の権限を持たないため上長の判断が必要
  if (申請.申請者.役職.kind === '一般社員') {
    要件.push({ kind: '役職なし申請' });
  }

  // 先方負担申請: 接待との境界が曖昧になるため不適切な支出を防ぐ事前チェックが必要
  if (申請.出張予定.費用負担区分 === '先方負担') {
    要件.push({ kind: '先方負担申請' });
  }

  if (要件.length > 0) {
    return { kind: '事前承認必要', 申請済み: 申請, 事前承認要件: 要件 };
  }
  return { kind: '事前承認不要', 申請済み: 申請 };
}

// ... 省略
```

事前承認要件が条件式の羅列ではなく型として表現され、Why コメントが各分岐に残されています。書籍8.6.2 の通り、Why をプロンプトに含めた効果が出ています。

## 参照

- [../../../ai-collaboration/core-generation.md](../../../ai-collaboration/core-generation.md)
- [../../../ai-collaboration/shell-generation.md](../../../ai-collaboration/shell-generation.md)
- [../../../ai-collaboration/verification-loop.md](../../../ai-collaboration/verification-loop.md)
- 書籍 8.3.2節（Core/Shell の二段階生成）、8.6節（Strict Spec / Policy & Discretion）
