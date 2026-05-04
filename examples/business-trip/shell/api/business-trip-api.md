---
name: 出張申請 API
description: Core の behavior に対応する REST API 契約の例
status: approved
last-reviewed: 2026-04-25
---

# 出張申請 API

[仕様モデル](../../spec-model/business-trip.md) の `behavior` を REST API として公開する例です。

## エンドポイントと behavior の対応

| HTTP | パス                                         | 対応する behavior              |
| ---- | -------------------------------------------- | ------------------------------ |
| POST | `/api/v1/business-trips`                     | 出張申請する                   |
| POST | `/api/v1/business-trips/{id}/submit`         | 申請する（ドラフト→申請済み） |
| GET  | `/api/v1/business-trips/{id}`                | 取得（射影）                   |
| POST | `/api/v1/business-trips/{id}/pre-approve`    | 上長が事前承認する             |
| POST | `/api/v1/business-trips/{id}/actuals`        | 出張実績を登録する             |
| POST | `/api/v1/business-trips/{id}/final-approve`  | 最終承認する                   |

## POST /api/v1/business-trips/{id}/pre-approve

### 対応する behavior

```text
behavior 上長が事前承認する =
  事前承認必要な出張申請 AND 承認者 AND 承認日時 -> 事前承認OK OR 事前承認NG
// 前提条件: 承認者が申請者の上長であること
```

### リクエスト

```text
認証: Bearer Token
認可: role >= MANAGER

POST /api/v1/business-trips/{id}/pre-approve
Content-Type: application/json

{
  "decision": "approve" | "reject",
  "rejectionReason": string  // decision = reject のときのみ必須
}
```

承認者は Bearer Token から取得します。

### レスポンス

#### 200 OK（事前承認OK）

```json
{
  "kind": "PreApproved",
  "id": "BT-2026-0001",
  "approver": "EMP-123",
  "approvedAt": "2026-04-25T10:00:00Z"
}
```

#### 200 OK（事前承認NG）

```json
{
  "kind": "PreApprovalRejected",
  "id": "BT-2026-0001",
  "approver": "EMP-123",
  "approvedAt": "2026-04-25T10:00:00Z",
  "rejectionReason": "予算オーバー"
}
```

#### 409 Conflict（状態不整合エラー）

事前承認必要でない申請に対して呼ばれた場合。

```json
{
  "kind": "InvariantViolation",
  "code": "NOT_PRE_APPROVAL_REQUIRED",
  "message": "この申請は事前承認が必要ありません"
}
```

#### 403 Forbidden（権限エラー）

承認者が申請者の上長でない場合。

```json
{
  "kind": "AuthorizationError",
  "code": "NOT_DIRECT_MANAGER",
  "message": "承認権限がありません"
}
```

## OpenAPI スキーマの所在

機械可読な契約は別ファイルで管理します（このサンプルでは省略）。

```text
api-spec/openapi.yaml の paths セクションに各エンドポイント定義
api-spec/components/schemas に Core の data から派生したスキーマ
```

## 契約テスト

[../../../reference/spec-set/spec-tests/totality/](../../../reference/spec-set/spec-tests/totality/) の規約に従い、各エンドポイントの全域性をテストします。

- 正常系: 事前承認必要な申請で、承認者が上長 → 事前承認OK が返る
- 拒否系: 事前承認必要な申請で、承認者が上長、却下理由あり → 事前承認NG が返る
- 状態不整合: 事前承認不要な申請に対して呼ぶ → 409 NOT_PRE_APPROVAL_REQUIRED
- 権限エラー: 承認者が上長ではない → 403 NOT_DIRECT_MANAGER

## 関連 Shell

- 永続: [../persistence/business-trip-table.md](../persistence/business-trip-table.md)
- UI: [../ui/business-trip-detail-screen.md](../ui/business-trip-detail-screen.md)
