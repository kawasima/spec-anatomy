# API 契約への変換規約

Core の `behavior` を HTTP/gRPC のエンドポイントに対応させ、入出力 `data` を OpenAPI/Protobuf スキーマに変換する規約です。

## 基本方針

API は Core の `behavior` をネットワーク越しに呼び出せる形にしたものです。エンドポイントごとに、対応する `behavior` を明示します。

- HTTP メソッドとパスを決める
- リクエストとレスポンスの型を Core の `data` から派生させる
- 認証・認可・エラーレスポンスを定義する
- OpenAPI などの機械可読な形式で契約を保存する

## エンドポイントと behavior の対応

```text
# Core
behavior 注文を承認する = 未承認注文 AND 承認者ID -> 承認済み注文 OR 承認エラー

# API
POST /api/v1/orders/{orderId}/approve
  認証: Bearer Token
  認可: role >= MANAGER
  リクエストボディ: 空（承認者IDは Bearer Token から取得）
  レスポンス:
    200 OK → 承認済み注文（Core の data から派生）
    409 Conflict → 承認エラー（INVARIANT_VIOLATION、INSUFFICIENT_ROLE）
    404 Not Found → 注文IDが存在しない
```

## リクエストとレスポンスの型

リクエストボディとレスポンスボディは、Core の `data` を JSON/Protobuf に変換します。Core の `OR` 分岐は、JSON では `kind` フィールド（discriminator）を使って表現します。

```text
# Core
data 承認結果 = 承認済み注文 OR 承認エラー

# JSON でのレスポンス
{
  "kind": "Approved",
  "orderId": "ORD-2026-0001",
  "approver": "EMP-123",
  "approvedAt": "2026-04-25T10:00:00Z"
}

または

{
  "kind": "ApprovalError",
  "code": "INSUFFICIENT_ROLE",
  "message": "承認権限がありません"
}
```

## エラーレスポンス

エラー分類（検証エラー／権限エラー／状態不整合エラー）を HTTP ステータスコードに対応させます。

| エラー種別          | 推奨される HTTP ステータス |
| ------------------- | -------------------------- |
| 検証エラー          | 400 Bad Request            |
| 権限エラー          | 401 / 403                  |
| 状態不整合エラー    | 409 Conflict               |
| リソース不在        | 404 Not Found              |
| サーバ側の障害      | 500 / 503                  |

エラーボディには `code`（エラーコード、Core のエラー型名と対応）と `message`（人間向けメッセージ、i18n される）を含めます。エラー詳細を呼び出し側がプログラムで判定できるよう、`code` は安定した識別子にします。

## 機械可読な契約の保管

OpenAPI、AsyncAPI、Protobuf などの機械可読な契約は別ファイルとして保存し、Markdown からは参照だけします。Markdown には「業務的な意味（Why）」を書き、機械可読な契約には「形式」を書きます。

```text
# api-spec/openapi.yaml — 形式
paths:
  /api/v1/orders/{orderId}/approve:
    post:
      ...

# docs/spec-set/shell/api/order-approve.md — 意味
このAPIは behavior 注文を承認する を呼び出すためのエンドポイントです。
顧客の注文を業務責任者が承認する操作で、業務上は ...
```

## 契約テスト

Core の `behavior` のシグネチャと、API のリクエスト/レスポンスが一致していることを契約テストで検証します。`behavior` の全域性テストを、API レイヤーでも適用します。

- リクエストボディが Core の入力 `data` の不変条件を満たすか
- レスポンスボディが Core の出力 `data` のどの枝に該当するか
- HTTP ステータスコードが Core のエラー種別と整合しているか

契約テストを CI で常時実行することで、Core を変更したのに API を更新し忘れる、という不整合を早期に検出します。

## 認証認可

認証・認可は Core の関心事ではなく Shell の関心事です。ただし「誰が何をできるか」というロール定義は Core の `behavior` に影響します。

```text
# Core: ロール定義は data として持つ
data ロール = 一般社員 OR マネージャー OR 部長

# Core: behavior が要求する権限を入力型で表現
behavior 上長が事前承認する =
  事前承認待ち AND マネージャー以上の承認者 -> 事前承認済み OR 承認エラー

# Shell（API）
POST /api/v1/business-trips/{id}/approve
  認証: Bearer Token
  認可: role >= MANAGER
```

「マネージャー以上」が業務的な要件なら Core 側に書き、認証方式（Bearer Token / mTLS / OAuth）は Shell 側に書きます。

## API のバージョニング

API のバージョニング（`/api/v1/`、`/api/v2/`）は Shell の関心事です。Core が変わるたびに新バージョンを切るのではなく、Core の変更が破壊的かどうか（拡張・制約強化・破壊的変更の3分類）で判断します。

- 拡張（OR の枝を追加） → 既存の API は壊れない。新枝を扱うクライアントだけが対応する
- 制約強化（Optional を必須化） → API のバリデーションが厳格化される。クライアントの修正が必要
- 破壊的変更 → 新バージョンの API を切る、または Expand and Contract で並行運用する

## テンプレート

- [templates/api.md](templates/api.md) — API 1件のテンプレート
- [templates/api-catalog.md](templates/api-catalog.md) — API 一覧

## 参照

- OpenAPI Specification
- AsyncAPI Specification
