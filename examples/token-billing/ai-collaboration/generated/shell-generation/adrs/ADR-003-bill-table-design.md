# ADR-003: `bills` を単一テーブル + `kind` 列 + CHECK 制約で表現する

## ステータス

採用（2026-05-02）

## 背景

Core の `Bill` は `sealed interface Bill = InQuota | WithOverage`。Shell 側でこれをどうテーブルに落とすかには、よくある3案がある。

- 案A: 単一テーブル + `kind` 列 + CHECK 制約（採用案）
- 案B: 別テーブル（`bills_in_quota`, `bills_with_overage`）+ 親 `bills` ビュー
- 案C: 単一テーブルで `overage_tokens = 0 ⇔ InQuota` という暗黙のルール（元素材のスタイル）

## 決定

案A を採用する。`bills` テーブルに `kind VARCHAR(16) NOT NULL CHECK (kind IN ('IN_QUOTA', 'WITH_OVERAGE'))` を置き、`InQuota` / `WithOverage` それぞれの形を CHECK 制約で表現する。

```sql
CONSTRAINT chk_in_quota_shape
    CHECK (kind <> 'IN_QUOTA' OR (
            overage_tokens              = 0
        AND applied_overage_rate_per_1k IS NULL
        AND total_charge                IS NULL
        AND included_tokens_used        = total_tokens
    )),
CONSTRAINT chk_with_overage_shape
    CHECK (kind <> 'WITH_OVERAGE' OR (
            overage_tokens              >= 1
        AND applied_overage_rate_per_1k IS NOT NULL
        AND total_charge                IS NOT NULL
        AND total_charge                > 0
    ))
```

## 理由

- 案C（元素材方式）は spec-model が refactoring で否定した「sentinel zero」設計。`overage_tokens = 0` を `InQuota` の代わりに使うと、レート列・請求列を「`InQuota` のときは 0 を入れる」にせざるをえず、以下が壊れる：
  - レートを変更した瞬間に過去の `InQuota` 行のレートが再現できない
  - 集計クエリで毎回「ゼロは超過なし」を判定し直す
  - sealed interface の二分割と DB スキーマの形が一致しない
- 案B（別テーブル）は分離としては綺麗だが、本サンプルで `bills` を読む唯一のクエリ「当月の `total_tokens` を集計する」は両ケースを区別せずに単純合計するもの。別テーブルにすると毎回 UNION する必要があり、コストの増加に見合うメリットがない。共通カラムも8/11と多く、外部キー（`customer_id`, `applied_pricing_plan_id`）も両方にぶら下がるため、参照整合性の宣言が二重になる。
- 案A は CHECK 制約で「sealed interface の場合分け」を DB スキーマに直接表現できる。`MapBillDecoders.BILL_ROW` は `kind` を見て `InQuota` / `WithOverage` のどちらの行デコーダにディスパッチする — Java 側の sealed switch と完全に対応する。
- 制約の存在自体が仕様書として読める。新しい開発者が `bills` を見たとき、`kind = 'IN_QUOTA' であれば total_charge IS NULL` がスキーマに直接書いてあれば、どこかのコードを読んで挙動を推測する必要がない。

## 影響

- `MapBillDecoders.BILL_ROW` は `kind` 値で分岐する単純な実装になる。
- `PgBillHistoryRepository.save(Bill)` は Java の `switch (bill)` で `InQuota` / `WithOverage` を分岐し、それぞれ別の INSERT 文を発行する。CHECK 制約があるため、ミスマッチな組合せ（`kind = 'IN_QUOTA'` だが `total_charge` を入れる、など）は DB が拒否する。
- 月次集計クエリ（`sumTotalTokensInMonth`）は `kind` を気にせず `SUM(total_tokens)` するだけでよい。
- 将来 `Bill` に第3のケース（例: `Refunded`）が増える場合は、`kind` の許容値と新しい CHECK 制約を1本追加すれば済む。テーブルを増やすマイグレーションは要らない。
