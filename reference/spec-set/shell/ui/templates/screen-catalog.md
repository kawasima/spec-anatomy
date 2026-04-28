---
name: 画面一覧
description: システム全体の画面の一覧
status: draft
last-reviewed: YYYY-MM-DD
---

# 画面一覧

システム全体で扱う画面の一覧です。Traditional SI 設計書の §6 画面一覧に対応します。

## 全画面一覧

| No | 画面ID | 画面名 | 画面説明 | 関連機能 | 関連ユースケース |
| --- | ------ | ------ | -------- | -------- | ---------------- |
| 1 | [SCREEN-001](SCREEN-001-<name>.md) | <画面名> | <概要> | <機能名> | `behavior <名前>` ([../../../spec-model/behavior/<file>.md](../../../spec-model/behavior/<file>.md)) |
| 2 | [SCREEN-002](SCREEN-002-<name>.md) | <画面名> | <概要> | <機能名> | `behavior <名前>` |

## カテゴリ別一覧

### 受注関連

| No | 画面ID | 画面名 | 画面説明 |
| --- | ------ | ------ | -------- |
| 1 | [SCREEN-100](SCREEN-100-<name>.md) | 注文一覧 | 受注した注文の一覧表示 |
| 2 | [SCREEN-101](SCREEN-101-<name>.md) | 注文詳細 | 個別注文の詳細表示と承認操作 |

### 在庫関連

| No | 画面ID | 画面名 | 画面説明 |
| --- | ------ | ------ | -------- |
| ... | ... | ... | ... |

## 命名規約

画面IDは次の形式で付けます。

- `SCREEN-{連番3桁}` または `SCREEN-{業務カテゴリ}-{連番3桁}`
- 例: `SCREEN-101`、`SCREEN-ORDER-001`

ファイル名は `SCREEN-{ID}-{kebab-case-name}.md` の形式にします。

- 例: `SCREEN-101-order-detail.md`

## 関連ドキュメント

- [screen-transitions.md](screen-transitions.md): 画面遷移
- 各画面の詳細: 上の表のリンク先
