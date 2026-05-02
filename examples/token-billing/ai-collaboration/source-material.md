---
name: token-billing 元素材
description: Spec Set を書き起こす素材として使った要件文書とテーブル定義
status: reference
last-reviewed: 2026-05-02
---

# token-billing 元素材

[gszhangwei/token-billing](https://github.com/gszhangwei/token-billing) リポジトリから、Spec Set 化の素材として参照した文書をそのまま転記したものです。Phase B（プロンプト評価）でも、各プロンプトに与える入力はこの素材だけにして、本サンプルとの差分を見ます。

## 元の要件文書（`requirements/token-usage-billing-story.md` 全文）

```markdown
## Background
The LLM API platform charges customers based on token consumption. Customers have monthly included quotas; usage exceeding the quota is billed at an overage rate.

## Business Value
1. **Accurate Billing**: Calculate charges based on actual token consumption.
2. **Quota Management**: Track usage against included quotas.
3. **Revenue Capture**: Bill overage when customers exceed quotas.

## Scope In
* Implement POST /api/usage endpoint for submitting token usage and receiving calculated bills.
* Request fields:
  * Customer ID (required, must exist)
  * Prompt tokens (required, ≥ 0)
  * Completion tokens (required, ≥ 0)
* Calculate bill using customer's monthly quota, current month usage, and overage rate.

## Scope Out
* Customer CRUD operations.
* Historical bill queries.
* Monthly quota reset logic.

## Acceptance Criteria (ACs)
1. Validate Customer ID exists
   **Given** customer ID does not exist
   **When** backend receives request
   **Then** return HTTP 404, message "Customer not found".

2. Validate token counts are non-negative
   **Given** prompt tokens or completion tokens is negative
   **When** backend validates request
   **Then** return HTTP 400, message "Token count cannot be negative".

3. Bill within included quota
   **Given** customer has 100,000 monthly quota and 60,000 tokens used this month
   **When** submitting 30,000 tokens
   **Then** bill shows: 30,000 from quota, 0 overage, $0.00 charge.

4. Bill exceeding included quota
   **Given** customer has 100,000 monthly quota, 80,000 tokens used this month, overage rate $0.02 per 1K tokens
   **When** submitting 50,000 tokens
   **Then** bill shows: 20,000 from quota, 30,000 overage, $0.60 charge.

5. Successful return
   **Given** valid request
   **When** bill is calculated
   **Then** return HTTP 201 with bill details including: bill ID, customer ID, total tokens, tokens from quota, overage tokens, total charge, and calculation timestamp.
```

## 元のテーブル定義（`src/main/resources/db/migration/V1__Create_tables.sql` 全文）

```sql
-- customers: basic info only
CREATE TABLE customers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- pricing_plans: reusable pricing configurations
CREATE TABLE pricing_plans (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    monthly_quota INTEGER NOT NULL,
    overage_rate_per_1k DECIMAL(10, 4) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- customer_subscriptions: customer-plan relationships
CREATE TABLE customer_subscriptions (
    id UUID PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(id),
    plan_id VARCHAR(50) NOT NULL REFERENCES pricing_plans(id),
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- bills: usage data and calculated billing results
CREATE TABLE bills (
    id UUID PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(id),
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    included_tokens_used INTEGER NOT NULL,
    overage_tokens INTEGER NOT NULL,
    total_charge DECIMAL(10, 2) NOT NULL,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## 元の README から抜粋した補足ルール

```text
1. Total tokens = prompt tokens + completion tokens
2. Included tokens first: Consume monthly quota before charging overage
3. Overage calculation: (overage tokens / 1000) × overage rate per 1K
```

## 元素材から本サンプルへの追加判断

要件文書とテーブルだけからは導けず、Spec Set 化の過程で**意図的に補ったもの**を記録しておきます。Phase B のプロンプト評価では、これらが各プロンプトの出力に現れるかを観察します。

- **型分割**: 「枠内請求 OR 超過込み請求」の二分割。元素材では `overage_tokens = 0` と「超過レート列なし」の暗黙の組合せだけで表現されている
- **適用超過レートの請求記録への記録**: 元のスキーマには列がない。プラン側のレートが将来変更された場合に過去の請求記録の意味が壊れるため追加
- **DB 制約の追加**: `chk_overage_consistency` `chk_total_tokens` `chk_token_split` などの整合性制約は元素材にはない
- **サブスクリプションなしケースの 409 応答**: 元の AC には書かれていないが、`有効な料金プランを取得する` が成功しないケースとして必要
- **月境界の明確化**: 元素材は `calculated_at` の TIMESTAMP のみで、暦月や TZ の扱いが書かれていない。本サンプルでは「UTC 暦月」を Shell の前提として固定した
- **通貨丸めの規則**: 元素材は `DECIMAL(10, 2)` の精度のみで丸め方の指定なし。`round_half_up` を採用した

これらは Core/Shell 双方で「元素材に書かれていなかった暗黙の前提」を仕様として明示化するという作業です。プロンプト評価では、各プロンプトがどこまで暗黙の前提を炙り出せるかを見ます。

## 関連

- Spec Set 全体: [../README.md](../README.md)
- 評価レポート（Phase B 完了時に追記）: [evaluation.md](evaluation.md)
