---
name: 出張申請 API
description: Core の behavior に対応する REST API 契約の例
status: approved
last-reviewed: 2026-04-25
---

# 出張申請 API

[仕様モデル](../../spec-model/business-trip.md) の `behavior` を REST API として公開する例です。

## エンドポイントと behavior の対応

| HTTP   | パス                                         | 対応する behavior                  |
| ------ | -------------------------------------------- | ---------------------------------- |
| POST   | `/api/v1/business-trips`                     | 下書きを保存する（新規）           |
| PUT    | `/api/v1/business-trips/{id}`                | 下書きを保存する（更新）           |
| DELETE | `/api/v1/business-trips/{id}`                | 下書きを破棄する                   |
| POST   | `/api/v1/business-trips/{id}/submit`         | 出張申請する（ドラフト→申請済み） |
| POST   | `/api/v1/business-trips/{id}/resubmit`       | 差し戻された申請を再申請する       |
| POST   | `/api/v1/business-trips/{id}/cancel`         | 出張申請を取り消す                 |
| GET    | `/api/v1/business-trips/{id}`                | 取得（射影）                       |
| POST   | `/api/v1/business-trips/{id}/pre-approve`    | 上長が事前承認する                 |
| POST   | `/api/v1/business-trips/{id}/actuals`        | 出張実績を登録する                 |
| POST   | `/api/v1/business-trips/{id}/final-approve`  | 最終承認する                       |

承認者の決定（`behavior 承認者を決定する`）は独立したエンドポイントを持ちません。`submit` / `resubmit` の内部で申請済みに遷移させたのち、`事前承認が必要か判断する` が「事前承認必要」を返した場合にサーバ側で承認者を解決し、`事前承認必要な出張申請` の approver として埋めます（上長 → 不在なら所属部門の部門長）。双方不在なら 409 `NO_APPROVER_FOUND` を返します（[承認者を決定する](#承認者決定の扱い) 参照）。

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

## PUT /api/v1/business-trips/{id}（下書きを保存する）

### 対応する behavior

```text
behavior 下書きを保存する = 出張予定 AND 申請者 -> 出張申請ドラフト
// 新規・更新の両方。何度でも呼べる（べき等）。バリデーションはドラフトなので緩い
```

新規作成は `POST /api/v1/business-trips`、既存ドラフトの更新は `PUT /api/v1/business-trips/{id}`。どちらも `出張申請ドラフト` を返します。

### リクエスト

```text
認証: Bearer Token
認可: 申請者本人のみ（他者のドラフトは 403）

PUT /api/v1/business-trips/{id}
Content-Type: application/json

{
  "purpose": string,
  "period": { "start": "2026-05-01", "end": "2026-05-03" },
  "travelers": [ "EMP-123", "EMP-456" ],   // 出張者（複数）
  "costBearing": "self" | "counterparty",
  "plannedCosts": [ { "date": "...", "category": "...", "amount": 0 } ]
}
```

申請者は Bearer Token から取得します。ドラフトなので未入力項目があっても保存できます。

### レスポンス

#### 200 OK（出張申請ドラフト）

```json
{
  "kind": "Draft",
  "id": "BT-2026-0001",
  "purpose": "...",
  "travelers": ["EMP-123", "EMP-456"]
}
```

#### 409 Conflict（状態不整合エラー）

ドラフト以外（申請済み以降）の申請に対して呼ばれた場合。

```json
{
  "kind": "InvariantViolation",
  "code": "NOT_DRAFT",
  "message": "この申請は下書きではないため編集できません"
}
```

## DELETE /api/v1/business-trips/{id}（下書きを破棄する）

### 対応する behavior

```text
behavior 下書きを破棄する = 出張申請ドラフト -> Unit
// ドラフトを物理削除する。取消（cancel）とは別。未提出の申請は破棄で消す
```

### リクエスト

```text
認証: Bearer Token
認可: 申請者本人のみ（他者のドラフトは 403）

DELETE /api/v1/business-trips/{id}
```

### レスポンス

#### 204 No Content

削除完了。ボディなし。

#### 409 Conflict（状態不整合エラー）

ドラフト以外の申請に対して呼ばれた場合。取消したい場合は `cancel` を使う。

```json
{
  "kind": "InvariantViolation",
  "code": "NOT_DRAFT",
  "message": "下書き以外は破棄できません。取消は取消操作を使ってください"
}
```

## POST /api/v1/business-trips/{id}/resubmit（差し戻された申請を再申請する）

### 対応する behavior

```text
behavior 差し戻された申請を再申請する =
  事前承認NG AND 出張予定 AND 申請日時 -> 申請済み出張申請
// 却下（差し戻し）された申請を申請者が修正して再提出する
// 全域性: 出力は申請済み出張申請の1枝。再提出後は再び事前承認要否判定にかかる
```

### リクエスト

```text
認証: Bearer Token
認可: 申請者本人のみ（他者の申請は 403）

POST /api/v1/business-trips/{id}/resubmit
Content-Type: application/json

{
  "purpose": string,
  "period": { "start": "...", "end": "..." },
  "travelers": [ "EMP-123" ],
  "costBearing": "self" | "counterparty",
  "plannedCosts": [ ... ]
}
```

修正後の出張予定を丸ごと送ります。申請日時はサーバ側で再採番します。

### レスポンス

#### 200 OK（申請済み出張申請）

```json
{
  "kind": "Submitted",
  "id": "BT-2026-0001",
  "submittedAt": "2026-04-28T09:00:00Z"
}
```

再申請後、サーバは続けて `事前承認が必要か判断する` を実行し、必要なら承認者を解決して `事前承認必要な出張申請` に着地させます。

#### 409 Conflict（状態不整合エラー）

`事前承認NG`（差し戻し）以外の申請に対して呼ばれた場合。

```json
{
  "kind": "InvariantViolation",
  "code": "NOT_REJECTED",
  "message": "差し戻された申請ではないため再申請できません"
}
```

#### 409 Conflict（承認者不在）

再申請後の要否判定で事前承認必要となったが、上長も部門長も解決できない場合。

```json
{
  "kind": "InvariantViolation",
  "code": "NO_APPROVER_FOUND",
  "message": "承認者（上長・部門長）が設定されていません"
}
```

## POST /api/v1/business-trips/{id}/cancel（出張申請を取り消す）

### 対応する behavior

```text
behavior 出張申請を取り消す =
  (申請済み出張申請 OR 事前承認必要な出張申請 OR 事前承認不要な出張申請
   OR 事前承認OK OR 事前承認NG OR 出張実績) AND 取消日時 -> 取消済出張申請
// 最終承認前まで、申請者が申請を取り下げられる
// Why: 出張中止・計画変更で不要になった申請を残さない。ただし最終承認済み・経理連携済みは取消不可
```

取消可能範囲は申請済み（'10'）〜出張実績（'40'）まで。ドラフト（'00'）は取消でなく破棄（DELETE）、最終承認済み（'50'）以降は取消不可。

### リクエスト

```text
認証: Bearer Token
認可: 申請者本人のみ（他者の申請は 403）

POST /api/v1/business-trips/{id}/cancel
```

取消日時はサーバ側で採番します。

### レスポンス

#### 200 OK（取消済出張申請）

```json
{
  "kind": "Cancelled",
  "id": "BT-2026-0001",
  "cancelledAt": "2026-04-28T12:00:00Z"
}
```

#### 409 Conflict（状態不整合エラー）

最終承認済み・経理連携済み・既に取消済みの申請に対して呼ばれた場合。

```json
{
  "kind": "InvariantViolation",
  "code": "NOT_CANCELLABLE",
  "message": "最終承認後の申請は取り消せません"
}
```

## 承認者決定の扱い

`behavior 承認者を決定する = 申請者 -> 承認者` は独立したエンドポイントを持たず、`submit` / `resubmit` の処理の一部としてサーバ側で実行されます。要否判定が「事前承認必要」を返したときにのみ承認者を解決し、`事前承認必要な出張申請` の approver に埋めます。

解決順序と失敗時の扱い。

```text
1. 申請者の上長を解決（EmployeeRepository.findManager）
2. 上長が不在なら所属部門の部門長を解決（DepartmentRepository.findManagerByEmployee）
3. 双方とも不在なら 409 NO_APPROVER_FOUND
```

Why: 承認は指揮命令系統の上位者が行う。上長未設定者も部門長が代行できるようにして承認の空白を作らない。永続側の参照解決は [永続モデル](../persistence/business-trip-table.md#承認者解決の永続的観点) を参照。

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
- 下書き保存: ドラフトを PUT → Draft が返る。ドラフト以外を PUT → 409 NOT_DRAFT
- 下書き破棄: ドラフトを DELETE → 204。ドラフト以外を DELETE → 409 NOT_DRAFT
- 再申請: 事前承認NG を resubmit → Submitted が返る。差し戻し以外を resubmit → 409 NOT_REJECTED
- 取消: 申請済み〜出張実績を cancel → Cancelled が返る。最終承認後を cancel → 409 NOT_CANCELLABLE
- 承認者決定: 上長不在だが部門長ありの申請者が submit → 部門長が approver に入る。上長も部門長も不在 → 409 NO_APPROVER_FOUND

## 関連 Shell

- 永続: [../persistence/business-trip-table.md](../persistence/business-trip-table.md)
- UI: [../ui/business-trip-detail-screen.md](../ui/business-trip-detail-screen.md)
