# 永続テンプレート

Shell の永続モデル（テーブル定義、コード値、マイグレーション）を埋めるためのテンプレートです。Traditional SI 設計書の §11.2 テーブル定義書、§10 コード設計書、§11.4 採番一覧を下敷きにしています。

## テンプレート一覧

- [table.md](table.md) — テーブル1件のテンプレート
- [table-catalog.md](table-catalog.md) — テーブル一覧のテンプレート
- [code.md](code.md) — コード値（enum）のテンプレート
- [identifiers.md](identifiers.md) — ID 体系・採番規則のテンプレート

## Core との関係

永続モデルは Core の `data` を永続化するための型です。永続モデルとドメインモデル（Core）は別の型として持ちます。

- 永続モデルが守るのは「レコード不変条件」（NOT NULL、PRIMARY KEY、FOREIGN KEY、CHECK）
- ドメインモデル（Core）が守るのは「ビジネス不変条件」

両者の対応は Mapper が担います。

## OR で状態を分けた data の永続化

Core で `data 注文 = 未承認注文 OR 承認済み注文 OR 出荷済み注文` のように状態ごとに型を分けても、永続モデルでは status カラム + 状態依存項目を NULL 可で表現するのが現実的です。Mapper で双方向に変換します。

```text
# Core
data 注文 = 未承認注文 OR 承認済み注文
data 未承認注文 = 注文番号 AND 顧客 AND 金額
data 承認済み注文 = 注文番号 AND 顧客 AND 金額 AND 承認者 AND 承認日時

# 永続モデル（テーブル定義）
CREATE TABLE orders (
  id, customer_id, amount, status,
  approver_id (NULL可),  -- status='approved' のとき必須
  approved_at (NULL可)   -- status='approved' のとき必須
);

# Mapper
toEntity(record):
  if record.status = 'approved' then 承認済み注文(...) else 未承認注文(...)
toRecord(entity):
  match entity {
    case 未承認注文 => { status: 'pending', approver_id: null, approved_at: null }
    case 承認済み注文 => { status: 'approved', approver_id: ..., approved_at: ... }
  }
```

## イミュータブルデータモデルの永続化

Core でイベント・エンティティを採るときは、イベントテーブルを INSERT-ONLY で運用します。

```text
CREATE TABLE order_events (
  event_id BIGINT PRIMARY KEY,
  order_id BIGINT NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  payload JSONB NOT NULL,
  occurred_at TIMESTAMP NOT NULL
);
-- INSERT-ONLY、UPDATE/DELETE しない
```

リソースの現在像を保持するテーブルは、イベントから導出されるスナップショットとして扱います。書き込みは Core の `behavior` を経由してイベントを発行し、リソーステーブルへの直接 UPDATE は避けます。

## 派生元の書き方

各カラムが Core のどの `data` のどの属性に対応するかを明示します。

```text
| カラム名     | 型         | NULL | 業務的意味              | 派生元                     |
| ------------ | ---------- | ---- | ----------------------- | -------------------------- |
| customer_id  | bigint     | NOT NULL | 顧客ID              | `承認済み注文.顧客.id`     |
| amount       | decimal    | NOT NULL | 注文金額            | `承認済み注文.金額`        |
| approver_id  | bigint     | NULL  | 承認者ID（承認時必須）| `承認済み注文.承認者.id`   |
```

派生元のないカラムが出てきたら、それは Core に追加すべき業務概念です。

## 参照

- [../README.md](../README.md): 永続変換規約
- [../../../examples/business-trip/shell/persistence/business-trip-table.md](../../../examples/business-trip/shell/persistence/business-trip-table.md): テンプレートを使ったサンプル
