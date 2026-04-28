# Core からのコード生成（Strict Spec）

仕様モデル（Core）からエージェントに実装コードを生成させる規約です。Strict Spec の流儀に従います。

## 原則：本質的複雑さは曖昧さゼロで渡す

業務ルール（事前承認の判定、精算額の計算、状態遷移、業務不変条件）は、エージェントに「補完」させてはいけません。曖昧な指示で渡すと、エージェントは学習データから「もっともらしい」答えを補完しますが、特定のドメインルールと一致する確率は低く、手戻りの原因になります。

仕様DSL を Strict Spec として、曖昧さゼロで渡します。

## 悪いプロンプトと良いプロンプト

### 悪いプロンプト

```text
出張申請の承認機能を実装してください。
金額が高い場合は上長の承認が必要です。
```

「高い」の閾値、「上長」の定義、承認フローのステップ、すべてが曖昧です。エージェントは「10万円」や「Manager」を勝手に選択しますが、業務と一致する保証がありません。

### 良いプロンプト

```text
次の仕様モデルを TypeScript で実装してください。

[ここに仕様DSL のコードブロックをそのまま貼る]
[判定規則の Why コメントも含める]

実装方針:
- 言語: TypeScript（strict モード）
- 型: 判別共用体（tagged union）と readonly な型を使う
- 各状態型には kind プロパティを持たせる
- behavior のシグネチャは仕様モデルのとおり入出力の型を限定する
- エラー処理: 例外を投げず、Result 型で失敗を表現する
```

エージェントはビジネスルールを推論する必要がなく、モデルをコードに変換する作業に集中します。

## 渡すもの

### 仕様DSL のコードブロック

`spec-model/data/` と `spec-model/behavior/` の該当部分を、Markdown コードブロックのまま渡します。

```text
data 出張申請 = 申請準備中 OR 事前承認待ち OR 事前承認済み
data 申請準備中 = 出張申請共通項目
data 事前承認待ち = 出張申請共通項目 AND 提出日時 AND 事前承認理由リスト AND 承認者ID
data 事前承認済み = 出張申請共通項目 AND 提出日時 AND 事前承認日時 AND 承認者ID

behavior 事前承認する = 事前承認待ち AND 承認者ID -> 事前承認済み OR 承認エラー
// 前提条件: 承認者IDが申請者の上長IDと一致すること
```

### Why コメント

判定規則の理由を必ず含めます。Why を渡すかどうかでエージェントが生成するコードの形が変わります。

```text
behavior 事前承認が必要か判断する =
  申請済み出張申請 -> 事前承認必要な出張申請 OR 事前承認不要な出張申請

// 事前承認要件:
// - 高額出張(予定費用合計 >= 100,000円)
//   理由: 高額支出は組織として事前に妥当性を確認する必要がある
// - 役職なし(申請者.役職 = なし)
//   理由: 役職なしの社員は支出判断の権限を持たないため上長の判断が必要
// - 先方負担(費用負担区分 = 先方負担)
//   理由: 接待との境界が曖昧になるため不適切な支出を防ぐ事前チェックが必要
```

Why のない `cost >= 100000` のような条件は、エージェントが条件式の羅列として実装します。Why があると、`HighCost`、`LackOfAuthority`、`ExternalCostBearing` のような型として要件を表現します。

### ユビキタス言語

用語の業務的意味と近接概念との違いを `spec-model/ubiquitous-language.md` から渡します。命名の揺れを防ぐためです。

## 渡さないもの

### 実装の詳細手順

「if 文で 100000 と比較して...」のようなマイクロマネジメントは、エージェントの実装パターン選択能力を阻害します。判別共用体・状態遷移・型レベル制約のような実装イディオムは、方針として渡しエージェントに任せます。

### ライブラリの選定

「zod を使え」「io-ts を使え」のような細かいライブラリ指定は、Shell 側の関心事です。Core 生成時には言語と型の使い方の方針だけを渡します。

## Phase 1: Core の実装

Core/Shell 二段階生成の Phase 1 として、Core の実装を Shell より先に行います。

### 制約

- フレームワーク、データベース、UIライブラリへの依存を一切禁止
- 標準ライブラリのみ
- 外部依存（API呼び出し、DB アクセス、メール送信）は引数として注入する形にする
- 純粋関数と業務概念を表す型のみ

### プロンプト例

```text
次の仕様モデルを Phase 1（Core）として TypeScript で実装してください。

[仕様DSL のコードブロック]

制約:
- 標準ライブラリのみ使用
- フレームワーク（Express、NestJS等）・データベースアクセス・UIライブラリは一切使わない
- 外部依存（API呼び出し、DB アクセス）は引数として注入する形にする
- 副作用を持つ behavior は明示的にマークする

実装方針:
- TypeScript の strict モード
- 判別共用体（tagged union）で OR を表現
- record 型と readonly で AND を表現
- Optional は省略可能なフィールドとして表現
- エラーは例外ではなく Result 型として表現

成果物:
- 型定義（data に対応）
- 純粋関数（behavior に対応）
- 副作用を持つ依存関数の型定義（インターフェースのみ）
```

### 期待される生成コード

```typescript
// 型定義（OR の判別共用体）
type BusinessTrip =
  | DraftBusinessTrip
  | AwaitingPreApprovalBusinessTrip
  | PreApprovedBusinessTrip;

type DraftBusinessTrip = {
  readonly kind: "Draft";
  readonly applicant: Employee;
  readonly estimatedCost: Money;
  readonly costBearingType: CostBearingType;
};

type PreApprovedBusinessTrip = {
  readonly kind: "PreApproved";
  readonly applicant: Employee;
  readonly estimatedCost: Money;
  readonly costBearingType: CostBearingType;
  readonly approver: EmployeeId;       // 必須
  readonly approvedAt: Date;            // 必須
};

// 純粋関数（behavior）
function preApprove(
  request: AwaitingPreApprovalBusinessTrip,
  approverId: EmployeeId
): PreApprovedBusinessTrip | ApprovalError {
  if (approverId !== request.applicant.managerId) {
    return { kind: "ApprovalError", reason: "InsufficientRole" };
  }
  return {
    kind: "PreApproved",
    applicant: request.applicant,
    estimatedCost: request.estimatedCost,
    costBearingType: request.costBearingType,
    approver: approverId,
    approvedAt: new Date(),
  };
}
```

## 検証

生成されたコードを次の観点で確認します。

- 仕様DSL の data 定義と TypeScript の型が1対1対応しているか
- 仕様DSL の behavior のシグネチャと TypeScript の関数のシグネチャが一致しているか
- フレームワーク・データベース・UIへの依存が混入していないか
- Why コメントが型名やバリアント名に反映されているか（条件式の羅列になっていないか）
- 全域性が保たれているか（すべての入力区分に対して結果が返るか）

仕様テストを生成して、Core の実装が仕様モデルと整合していることを継続的に検証します（[verification-loop.md](verification-loop.md)）。

## 参照

- Scott Wlaschin *Domain Modeling Made Functional*（型駆動の業務ロジック表現）
