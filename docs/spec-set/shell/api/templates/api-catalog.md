---
name: API 一覧
description: システム全体の API の一覧
status: draft
last-reviewed: YYYY-MM-DD
---

# API 一覧

システム全体で公開する API の一覧です。Traditional SI 設計書の §5 WebサービスAPI一覧に対応します。

## 概要

| 項目              | 値                          |
| ----------------- | --------------------------- |
| コンテキストルート | `/api`                      |
| API バージョン    | `v1`                        |
| 認証方式          | Bearer Token (JWT)          |
| データ形式        | JSON                        |
| 文字コード        | UTF-8                       |

## 全API一覧

| No | API_ID | API名称 | 処理概要 | プロトコル | HTTPメソッド | リクエストURL | データ形式 | 入力電文ID | 出力電文ID | 処理対象取引 |
| --- | ------ | ------- | -------- | ---------- | ------------ | ------------- | ---------- | ---------- | ---------- | ------------ |
| 1 | [API-001](API-001-<name>.md) | <API名> | <概要> | HTTPS | POST | `/api/v1/orders` | JSON | <入力ID> | <出力ID> | `behavior <名前>` ([../../../spec-model/behavior/<file>.md](../../../spec-model/behavior/<file>.md)) |
| 2 | [API-002](API-002-<name>.md) | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## カテゴリ別一覧

### 受注関連 API

| No | API_ID | API名称 | 処理概要 |
| --- | ------ | ------- | -------- |
| 1 | [API-100](API-100-<name>.md) | 注文を提出する | 顧客が注文を提出 |
| 2 | [API-101](API-101-<name>.md) | 注文を承認する | 業務責任者が事前承認 |
| 3 | [API-102](API-102-<name>.md) | 注文をキャンセルする | キャンセル処理 |

### 在庫関連 API

| No | API_ID | API名称 | 処理概要 |
| --- | ------ | ------- | -------- |
| ... | ... | ... | ... |

## 命名規約

API IDは次の形式で付けます。

- `API-{連番3桁}` または `API-{業務カテゴリ}-{連番3桁}`
- 例: `API-101`、`API-ORDER-APPROVE`

ファイル名は `API-{ID}-{kebab-case-name}.md` の形式にします。

## 機械可読契約の所在

OpenAPI 仕様は別ファイルで管理します。

- 仕様ファイル: `api-spec/openapi.yaml`
- 各 API の path 定義は API 個別ファイルから参照
