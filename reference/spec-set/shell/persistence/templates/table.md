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

| 論理カラム名 | 物理カラム名 | ドメイン名論理 | 型           | NULL     | PK 順序 | FK             | INDEX 順序 | 業務的意味     | 制約                  | 派生元                       |
| ------------ | ------------ | -------------- | ------------ | -------- | ------- | -------------- | ---------- | -------------- | --------------------- | ---------------------------- |
| 注文ID       | id           | 注文ID         | char(26)     | NOT NULL | 1       | -              | -          | 主キー         | ULID 形式             | `<data 名>.id`               |
| <論理名>     | <物理名>     | <ドメイン名>   | varchar(100) | NOT NULL | -       | -              | IDX1: 1    | <意味>         | <制約>                | `<data 名>.<属性>`           |
| <論理名>     | <物理名>     | <ドメイン名>   | bigint       | NOT NULL | -       | <参照テーブル> | IDX2: 1    | <意味>         | <制約>                | `<data 名>.<関連>.id`        |
| 状態         | status       | 注文状態       | varchar(20)  | NOT NULL | -       | -              | IDX3: 1    | 状態           | OrderStatus の値      | `<data 名>` の OR 分岐の判別 |
| <論理名>     | <物理名>     | <ドメイン名>   | bigint       | NULL     | -       | -              | -          | <状態依存項目> | status='X' のとき必須 | `<data 名>.<属性>`           |

PK順序は主キー内の列順を1始まりの整数で書きます。複合主キーがあるときに順序が業務上の意味を持つので、列として明示します。

INDEX順序は `<INDEX名>: <列順>` の形式で書きます。1つのカラムが複数のINDEXに含まれることもあるので、その場合は `IDX1: 2, IDX3: 1` のように列挙します。

ドメイン名論理は項目バリデーション（[../../persistence/templates/identifiers.md](../../persistence/templates/identifiers.md) のような ID 体系や、Bean Validation アノテーションに対応する論理名）の参照キーとして使います。Traditional SIの「ドメイン定義書」が持っていた役割を、ここで保持します。

## インデックス

| インデックス名 | 対象カラム（順序付き）       | 用途                 |
| -------------- | ---------------------------- | -------------------- |
| IDX1           | <物理名1>                    | <どのクエリで使うか> |
| IDX2           | <物理名2>(1), <物理名3>(2)   | <用途>               |

複合インデックスの場合は、対象カラムに列順を `(1)` `(2)` の形で添えます。

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
