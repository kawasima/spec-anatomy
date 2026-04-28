# API テンプレート

Shell の API 契約を埋めるためのテンプレートです。Traditional SI 設計書の §5 インタフェース設計（WebサービスAPI一覧、外部I/F設計書）を下敷きにしています。

## テンプレート一覧

- [api.md](api.md) — API 1件のテンプレート（業務的意味、対応する behavior、リクエスト・レスポンス、エラー、契約テスト）
- [api-catalog.md](api-catalog.md) — API 一覧（カタログ）のテンプレート

## OpenAPI との分担

API の機械可読な契約は OpenAPI（または gRPC の場合は .proto）として別ファイルで管理します。Markdown のテンプレートには次を書きます。

- 業務的な意味（Why）
- 対応する Core の `behavior` への参照
- 業務的事前条件・事後条件
- エラーレスポンスの業務的意味（HTTP ステータスコードへのマッピングを含む）
- 契約テストの所在

OpenAPI に書くこと（形式の詳細：パラメータ型、レスポンスボディの JSON Schema）は OpenAPI に委ねます。重複しません。

```text
# OpenAPI: api-spec/openapi.yaml — 形式
paths:
  /api/v1/orders/{orderId}/approve:
    post:
      ...

# Spec Set: shell/api/order-approve.md — 意味
このAPIは behavior 注文を承認する を呼び出すためのエンドポイントです。
顧客の注文を業務責任者が承認する操作で、業務上は ...
```

## 派生元の書き方

API のリクエストとレスポンスの型は、Core の `data` から派生します。

- リクエストボディ: Core の `behavior` の入力 `data` から派生
- レスポンスボディ（成功）: Core の `behavior` の出力（成功側）から派生
- レスポンスボディ（エラー）: Core の `behavior` の出力（失敗側）から派生

派生元のないフィールドが API に出てきたら、それは Core に追加すべき業務概念です。

## 参照

- [../README.md](../README.md): API 変換規約
- [../../../../docs/shell/api/business-trip-api.md](../../../../docs/shell/api/business-trip-api.md): API テンプレートを使ったサンプル
