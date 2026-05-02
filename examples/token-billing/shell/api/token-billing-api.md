---
name: トークン課金 API
description: Core の behavior に対応する REST API 契約
status: approved
last-reviewed: 2026-05-02
---

# トークン課金 API

[仕様モデル](../../spec-model/token-billing.md) の `behavior` を REST API として公開する契約です。元の要件文書では POST /api/usage 1 本のみが定義されていましたが、Spec Set としてはパス命名規則を `/api/v1/usage` に揃えています。

## エンドポイントと behavior の対応

| HTTP | パス                | 対応する behavior                                                       |
| ---- | ------------------- | ----------------------------------------------------------------------- |
| POST | `/api/v1/usage`     | 当月消費を取得する → 有効な料金プランを取得する → 請求を計算する → 請求記録を保存する |

このサービスは1エンドポイントで4つの behavior を順に呼ぶオーケストレーションです。各 behavior の失敗は HTTP のエラー応答に投影されます。

## POST /api/v1/usage

### 対応する behavior

```text
behavior 請求を計算する =
  当月消費 AND 料金プラン AND 申告トークン -> 枠内請求 OR 超過込み請求
```

API ハンドラは「顧客IDの存在確認」「申告トークンの非負検証」を入力境界として先に行い、その後 Core の behavior 群を順に呼び出します。

### リクエスト

```text
認証: API Key（このサンプルでは省略可）
認可: なし（顧客IDで識別）

POST /api/v1/usage
Content-Type: application/json

{
  "customerId": string,        // 必須、顧客IDが既存であること
  "promptTokens": integer,      // 必須、0以上
  "completionTokens": integer   // 必須、0以上
}
```

### レスポンス

#### 201 Created（枠内請求）

```json
{
  "kind": "InQuota",
  "billId": "550e8400-e29b-41d4-a716-446655440000",
  "customerId": "CUST-001",
  "promptTokens": 12000,
  "completionTokens": 18000,
  "totalTokens": 30000,
  "includedTokensUsed": 30000,
  "overageTokens": 0,
  "totalCharge": "0.00",
  "calculatedAt": "2026-05-02T10:00:00Z"
}
```

`kind: "InQuota"` のときは `overageTokens` は常に 0、`totalCharge` は常に "0.00" になります。これは Core の `枠内請求` 型に対応する射影で、JSON 上は互換のため0埋めしますが、意味としては「これらのフィールドは存在しない」ことを示しています。

#### 201 Created（超過込み請求）

```json
{
  "kind": "WithOverage",
  "billId": "660e8400-e29b-41d4-a716-446655440001",
  "customerId": "CUST-002",
  "promptTokens": 20000,
  "completionTokens": 30000,
  "totalTokens": 50000,
  "includedTokensUsed": 20000,
  "overageTokens": 30000,
  "appliedOverageRatePer1k": "0.0200",
  "totalCharge": "0.60",
  "calculatedAt": "2026-05-02T10:00:00Z"
}
```

`kind: "WithOverage"` のときは `overageTokens` ≥ 1、`appliedOverageRatePer1k` が必須、`totalCharge` > 0 が保証されます。

#### 400 Bad Request（入力検証エラー）

`promptTokens` または `completionTokens` が負の場合（AC2）。

```json
{
  "kind": "ValidationError",
  "code": "TOKEN_COUNT_NEGATIVE",
  "message": "Token count cannot be negative"
}
```

#### 404 Not Found（顧客なし）

`customerId` に対応する顧客が存在しない場合（AC1）。

```json
{
  "kind": "NotFound",
  "code": "CUSTOMER_NOT_FOUND",
  "message": "Customer not found"
}
```

#### 409 Conflict（サブスクリプションなし）

顧客は存在するが、当該日付に有効なサブスクリプションがない場合（要件文書には明記されていないが、Core の `有効な料金プランを取得する` が `サブスクリプションなし` を返したときの正当な経路）。

```json
{
  "kind": "InvariantViolation",
  "code": "NO_ACTIVE_SUBSCRIPTION",
  "message": "Customer has no active subscription on the calculation date"
}
```

## レスポンス型と Core 型の対応

| Core の型        | レスポンスの `kind` | `overageTokens` | `totalCharge` | `appliedOverageRatePer1k` |
| ---------------- | ------------------- | --------------- | ------------- | ------------------------- |
| 枠内請求         | `"InQuota"`         | 常に 0          | 常に "0.00"   | 含めない                  |
| 超過込み請求     | `"WithOverage"`     | ≥ 1             | > 0           | 必須                      |

JSON では Core の OR 分割を `kind` で識別するタグ付き union にします。クライアントは `kind` を見て分岐すれば、各バリアントで意味のあるフィールドだけを安全に参照できます。

## OpenAPI スキーマの所在

機械可読な契約は別ファイルで管理します（このサンプルでは省略）。

```text
api-spec/openapi.yaml の paths セクションに /api/v1/usage の定義
api-spec/components/schemas に Core の data から派生したスキーマ:
  - InQuotaBill, WithOverageBill, BillResponse(union)
  - ValidationError, NotFound, InvariantViolation
```

## 契約テスト

[../../../../reference/spec-set/spec-tests/totality/](../../../../reference/spec-set/spec-tests/totality/) の規約に従い、各エンドポイントの全域性をテストします。受け入れ基準（AC1〜AC5）に対応するケース:

- AC1: 存在しない顧客ID → 404 CUSTOMER_NOT_FOUND
- AC2: promptTokens = -1 → 400 TOKEN_COUNT_NEGATIVE
- AC3: 含み枠 100,000 / 当月消費 60,000 / 申告 30,000 → 201 InQuota, includedTokensUsed=30000, overageTokens=0, totalCharge="0.00"
- AC4: 含み枠 100,000 / 当月消費 80,000 / 申告 50,000 / レート $0.02 → 201 WithOverage, includedTokensUsed=20000, overageTokens=30000, totalCharge="0.60"
- AC5: 正常応答ヘッダ・ボディに billId / customerId / totalTokens / includedTokensUsed / overageTokens / totalCharge / calculatedAt が含まれる
- 追加: サブスクリプションなしの顧客 → 409 NO_ACTIVE_SUBSCRIPTION

## 関連 Shell

- 永続: [../persistence/token-billing-table.md](../persistence/token-billing-table.md)

## 関連 ADR（このサンプルでは省略）

- 通貨の丸め規則（half-up vs banker's）
- 月境界の扱い（UTC vs 顧客タイムゾーン）
