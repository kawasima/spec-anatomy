---
name: <テーブルの業務的名前>
description: <このテーブルが業務上保持するもの>
status: draft
last-reviewed: YYYY-MM-DD
---

# `<table-name>` テーブル

## このテーブルの業務的役割

<このテーブルが業務上何を保持するか。Core のどの `data` の永続化を担うか。3〜5文の散文で書く。>

## 関連する Core の data

- [`<data 名>`](../../../spec-model/data/<file>.md): このテーブルが永続化する Core の `data`

## サブシステム

- 主管サブシステム: <サブシステム名>

## カラム定義

| カラム名      | 型              | NULL     | PK | FK            | INDEX | 業務的意味           | 制約                       | 派生元                          |
| ------------- | --------------- | -------- | -- | ------------- | ----- | -------------------- | -------------------------- | ------------------------------- |
| id            | char(26)        | NOT NULL | ○  | -             | -     | 主キー               | ULID 形式                  | `<data 名>.id`                  |
| <column>      | varchar(100)    | NOT NULL | -  | -             | IDX1  | <意味>               | <制約>                     | `<data 名>.<属性>`              |
| <column>      | bigint          | NOT NULL | -  | <参照テーブル> | IDX2  | <意味>               | <制約>                     | `<data 名>.<関連>.id`           |
| <column>      | varchar(20)     | NOT NULL | -  | -             | IDX3  | 状態                 | OrderStatus の値           | `<data 名>` の OR 分岐の判別    |
| <column>      | bigint          | NULL     | -  | -             | -     | <状態依存項目>       | status='X' のとき必須      | `<data 名>.<属性>`              |

## インデックス

| インデックス名 | 対象カラム                | 用途                       |
| -------------- | ------------------------- | -------------------------- |
| IDX1           | <column1>                 | <どのクエリで使うか>       |
| IDX2           | <column2>, <column3>      | <用途>                     |

## 暗号化対象

個人情報や機密情報が含まれる場合のみ記述。

| カラム            | 暗号化方式      | 鍵管理         |
| ----------------- | --------------- | -------------- |
| <column>          | AES-256-GCM     | KMS            |

関連 ADR: [<ADR-XXX>](../../../adrs/<ADR-XXX>-encryption.md)

## 参照整合性

| 参照先テーブル | 参照カラム      | 業務的意味                   |
| -------------- | --------------- | ---------------------------- |
| <table>        | <column>        | <この参照が業務上何を表すか> |

外部キーを物理制約として張るか、アプリケーション側で整合性検査するかは ADR で決めます。

## CHECK 制約

業務不変条件のうち、テーブル単体で守れるものを CHECK 制約として書きます。

```sql
CHECK (amount >= 0)
CHECK (status IN ('pending', 'approved', 'shipped', 'completed', 'canceled'))
CHECK ((status = 'approved') = (approver_id IS NOT NULL))  -- 承認済みなら承認者必須
```

複数集約をまたぐ業務不変条件は、テーブル制約では表現できません。Core の仕様テスト（[../../../spec-tests/state-transitions/](../../../spec-tests/state-transitions/)）で property-based test を書きます。

## ライフサイクル

このテーブルへの操作と Core の `behavior` の対応。

| 操作   | Core の behavior              | 補足                              |
| ------ | ----------------------------- | --------------------------------- |
| INSERT | `behavior <名前>`             | <ID 採番タイミングを明示>         |
| UPDATE | `behavior <名前>`             | <どのカラムが更新されるか>        |
| DELETE | (使わない / 論理削除)         | <論理削除なら deleted_at カラム> |

イミュータブルデータモデルを採用している場合は、UPDATE/DELETE をしないことを明記。

## Mapper の責務

Core の `data` ⇔ レコードの変換規則を書きます。

### `<data 名>` → レコード

```text
toRecord(<data 名>):
  base = { id: ..., customer_id: ..., amount: ... }
  match <data 名> {
    case 未承認注文 => { ...base, status: 'pending', approver_id: null, approved_at: null }
    case 承認済み注文 => { ...base, status: 'approved', approver_id: ..., approved_at: ... }
  }
```

### レコード → `<data 名>`

```text
toEntity(record):
  match record.status {
    case 'pending' => 未承認注文(record.id, record.customer_id, record.amount)
    case 'approved' =>
      if record.approver_id = null then Mapping エラー
      else 承認済み注文(record.id, record.customer_id, record.amount, record.approver_id, record.approved_at)
    ...
  }
```

`approver_id` が NULL なのに status='approved' のような不整合データは Mapping エラーとして扱います。

## 関連の永続化パターン

このテーブルが他のテーブルと関連を持つ場合は、関連のモデリングの4論点（パリティ・ID/実体・取得タイミング・更新方式）の組み合わせを明示します。

| 関連テーブル | パリティ | 参照種別 | 取得タイミング | 更新方式       |
| ------------ | -------- | -------- | -------------- | -------------- |
| <table>      | 単方向   | 実体参照 | Eager Load     | 差分検出       |
| <table>      | 単方向   | ID参照   | 必要時取得     | DEL/INS        |

## マイグレーション

新規作成・変更の場合のマイグレーションスクリプトの所在。

- 初期作成: `db/migration/V001__create_<table>.sql`
- 変更履歴: `db/migration/V0XX__alter_<table>_<change>.sql`

仕様変更の3分類（拡張・制約強化・破壊的変更）と Expand and Contract の流儀に従い、段階的に変更します。

## 実装への対応

- DDL: `<マイグレーションファイルパス>`
- Entity: `<コード側の Entity クラスのパス>`
- Repository: `<コード側の Repository のパス>`
- Mapper: `<コード側の Mapper のパス>`

## 派生元参照のチェック

- すべてのカラムに Core の `data` からの派生元が書かれているか
- Core にないカラムをテーブル側で発明していないか
- 状態依存の必須項目（NULL 可カラム）が CHECK 制約で守られているか
