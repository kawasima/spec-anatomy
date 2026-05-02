---
name: トークン課金テーブル
description: Core の data に対応する永続モデル（Data Mapper パターン）
status: approved
last-reviewed: 2026-05-02
---

# トークン課金テーブル

[仕様モデル](../../spec-model/token-billing.md) の `data` を、永続モデルとしてどう表現するかの定義です。元の token-billing リポジトリの `V1__Create_tables.sql` をベースに、Spec Set の規約に沿って Core との対応を明示しています。

## 永続モデルとドメインモデルの分離

Data Mapper パターンに従い、永続モデル（テーブル）とドメインモデル（Core）を別の型として持ちます。Core の `請求 = 枠内請求 OR 超過込み請求` という型分割は、テーブル上では「単一テーブル + 必須カラム/任意カラム」で表現し、Mapper で双方向に変換します。

## テーブル定義

```sql
-- 顧客（Core: 顧客）
CREATE TABLE customers (
    id          VARCHAR(50) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 料金プラン（Core: 料金プラン）
CREATE TABLE pricing_plans (
    id                      VARCHAR(50) PRIMARY KEY,
    name                    VARCHAR(100) NOT NULL,
    monthly_quota           INTEGER NOT NULL,
    overage_rate_per_1k     DECIMAL(10, 4) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_quota_nonneg CHECK (monthly_quota >= 0),
    CONSTRAINT chk_rate_nonneg CHECK (overage_rate_per_1k >= 0)
);

-- サブスクリプション（Core: サブスクリプション）
CREATE TABLE customer_subscriptions (
    id              UUID PRIMARY KEY,
    customer_id     VARCHAR(50) NOT NULL REFERENCES customers(id),
    plan_id         VARCHAR(50) NOT NULL REFERENCES pricing_plans(id),
    effective_from  DATE NOT NULL,
    effective_to    DATE,                       -- NULL は無期限
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_effective_range CHECK (effective_to IS NULL OR effective_from <= effective_to)
);

-- 請求記録（Core: 請求記録）
CREATE TABLE bills (
    id                       UUID PRIMARY KEY,
    customer_id              VARCHAR(50) NOT NULL REFERENCES customers(id),
    prompt_tokens            INTEGER NOT NULL,
    completion_tokens        INTEGER NOT NULL,
    total_tokens             INTEGER NOT NULL,
    included_tokens_used     INTEGER NOT NULL,
    overage_tokens           INTEGER NOT NULL,           -- 枠内請求のときは 0
    applied_overage_rate_per_1k DECIMAL(10, 4),         -- 枠内請求のときは NULL
    total_charge             DECIMAL(10, 2) NOT NULL,    -- 枠内請求のときは 0.00
    calculated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tokens_nonneg CHECK (prompt_tokens >= 0 AND completion_tokens >= 0),
    CONSTRAINT chk_total_tokens CHECK (total_tokens = prompt_tokens + completion_tokens),
    CONSTRAINT chk_token_split CHECK (included_tokens_used + overage_tokens = total_tokens),
    CONSTRAINT chk_overage_consistency CHECK (
        (overage_tokens = 0 AND applied_overage_rate_per_1k IS NULL AND total_charge = 0.00)
        OR
        (overage_tokens > 0 AND applied_overage_rate_per_1k IS NOT NULL AND total_charge > 0.00)
    )
);

CREATE INDEX idx_customer_subscriptions_customer_id ON customer_subscriptions(customer_id);
CREATE INDEX idx_bills_customer_id ON bills(customer_id);
CREATE INDEX idx_bills_calculated_at ON bills(calculated_at);
```

元の token-billing スキーマからの差分:

- `bills.applied_overage_rate_per_1k` カラムを追加。Core の `超過込み請求.適用超過レート` をそのまま保存するため。元のスキーマでは料金プラン側の現在値から推測する形だが、レート変更後の請求記録の意味が壊れるため、計算時のレートを請求記録に固定する
- `chk_overage_consistency` 制約を追加。Core の「枠内請求 OR 超過込み請求」の OR 分割を、テーブル上の「3カラムの整合性」として宣言する
- `chk_total_tokens` `chk_token_split` 制約を追加。`total_tokens = prompt + completion` および `included + overage = total` を DB レベルで保証

## Mapper の責務

### Core → 永続モデル（toRecord）

```text
behavior toRecord = 請求記録 -> BillRecord

# 枠内請求 (InQuota) の場合
枠内請求 → {
  prompt_tokens = 申告.プロンプト, completion_tokens = 申告.補完,
  total_tokens = 合計, included_tokens_used = 合計,
  overage_tokens = 0,
  applied_overage_rate_per_1k = NULL,
  total_charge = 0.00
}

# 超過込み請求 (WithOverage) の場合
超過込み請求 → {
  prompt_tokens = 申告.プロンプト, completion_tokens = 申告.補完,
  total_tokens = 合計, included_tokens_used = 枠内消費,
  overage_tokens = 超過,
  applied_overage_rate_per_1k = 適用超過レート,
  total_charge = 請求額
}
```

### 永続モデル → Core（toEntity）

```text
behavior toEntity = BillRecord -> 請求記録 OR Mapping エラー

# 制約 chk_overage_consistency により、次の2パターンしか存在しない
overage_tokens = 0 AND applied_overage_rate_per_1k IS NULL → 枠内請求
overage_tokens > 0 AND applied_overage_rate_per_1k IS NOT NULL → 超過込み請求

# それ以外の組合せ（DB 制約をすり抜けて入った場合）→ Mapping エラー
```

DB 制約と Mapper の両方で同じ判別を持つことで、データが壊れていれば Mapper 段で確実に検知できます。

## 当月消費の計算

Core の `当月消費を取得する` は、DB 上は `bills` テーブルへの集約クエリとして実装します。

```sql
SELECT COALESCE(SUM(total_tokens), 0) AS this_month_total
FROM bills
WHERE customer_id = :customerId
  AND calculated_at >= :month_start
  AND calculated_at <  :next_month_start;
```

月境界（`month_start` `next_month_start`）はサーバの UTC で扱うことを想定しますが、これは ADR で確定すべき決定です。元の要件文書には書かれていないので、このサンプルでは「UTC、暦月単位」を Shell の前提として固定しています。

## 関連の永続化

| 関連                                | 種類           | 永続化パターン                |
| ----------------------------------- | -------------- | ----------------------------- |
| 顧客 ⇔ サブスクリプション           | 親子（独立寿命）| 別テーブル + 顧客IDで参照     |
| サブスクリプション → 料金プラン     | リソース参照   | プランIDで参照                |
| 顧客 ⇔ 請求記録                     | 親子（独立寿命）| 別テーブル + 顧客IDで参照     |
| 請求記録 → 適用超過レート           | 値の埋め込み   | 請求記録テーブルに値をコピー  |

サブスクリプションと請求記録は顧客のライフサイクルに従属しないため、それぞれ独立した集約として扱います。料金プランは複数顧客から参照される共有リソースで、請求記録には「計算時のレート」をコピーして保存することで、レート変更の影響を過去の請求記録に及ぼしません。

## Repository インターフェース

```text
behavior CustomerRepository.findById = 顧客ID -> 顧客 OR NotFound

behavior SubscriptionRepository.findActive =
  顧客ID AND 日付 -> サブスクリプション OR サブスクリプションなし
// effective_from <= 日付 AND (effective_to IS NULL OR 日付 <= effective_to) で抽出

behavior PricingPlanRepository.findById = プランID -> 料金プラン OR NotFound

behavior BillRepository.findThisMonthTotal =
  顧客ID AND 月 -> トークン数  // 集約クエリ。レコードが0件なら 0

behavior BillRepository.save = 請求記録 -> 保存完了
```

## 関連 Shell

- API: [../api/token-billing-api.md](../api/token-billing-api.md)

## 関連 ADR（このサンプルでは省略）

- 通貨の丸め規則（half-up vs banker's）
- 月境界の扱い（UTC vs 顧客タイムゾーン vs サーバローカル）
- レート変更の遡及反映の有無（このサンプルでは「請求記録に値をコピーして遡及しない」を採用）
