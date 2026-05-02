-- ============================================================
-- token-billing schema (Shell layer)
--
-- Derived from the original V1__Create_tables.sql in source-material.md,
-- with the following spec-model-driven additions:
--   * bills.kind                       — discriminator for InQuota / WithOverage
--   * bills.applied_overage_rate_per_1k — snapshotted at calculation time
--   * CHECK constraints                — encode the sealed-interface invariants
--                                        (a WithOverage row must carry rate, charge,
--                                         positive overage_tokens; an InQuota row must
--                                         leave them NULL and have zero overage)
--   * NOT NULL on customer_subscriptions(plan_id) — already present, kept explicit
--
-- Why these additions: the spec-model splits 請求 into 枠内請求 OR 超過込み請求.
-- The integer-zero sentinel of the original schema (overage_tokens = 0 means in-quota)
-- conflates the two states. We restore the distinction by adding a `kind` column
-- and CHECK constraints that make a malformed mix structurally unrepresentable —
-- the same guarantee the Java sealed interface gives us, lifted to the database.
-- See adrs/ADR-003-bill-table-design.md for the alternative (separate tables) we rejected.
-- ============================================================

-- customers: basic info only
CREATE TABLE customers (
    id          VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- pricing_plans: reusable pricing configurations
CREATE TABLE pricing_plans (
    id                   VARCHAR(50)    PRIMARY KEY,
    name                 VARCHAR(100)   NOT NULL,
    monthly_quota        BIGINT         NOT NULL CHECK (monthly_quota >= 0),
    overage_rate_per_1k  DECIMAL(10, 4) NOT NULL CHECK (overage_rate_per_1k >= 0),
    created_at           TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- customer_subscriptions: customer-plan relationships
CREATE TABLE customer_subscriptions (
    id              UUID         PRIMARY KEY,
    customer_id     VARCHAR(50)  NOT NULL REFERENCES customers(id),
    plan_id         VARCHAR(50)  NOT NULL REFERENCES pricing_plans(id),
    effective_from  DATE         NOT NULL,
    effective_to    DATE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_effective_period CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE INDEX idx_customer_subscriptions_customer_effective
    ON customer_subscriptions (customer_id, effective_from, effective_to);

-- bills: usage data and calculated billing results
--
-- Bill = InQuota | WithOverage  (sealed interface in Core)
--   InQuota:
--     kind = 'IN_QUOTA'
--     overage_tokens                = 0
--     applied_overage_rate_per_1k   IS NULL
--     total_charge                  IS NULL
--     included_tokens_used          = total_tokens
--   WithOverage:
--     kind = 'WITH_OVERAGE'
--     overage_tokens                >= 1
--     applied_overage_rate_per_1k   IS NOT NULL
--     total_charge                  > 0
--     included_tokens_used + overage_tokens = total_tokens
CREATE TABLE bills (
    id                            UUID           PRIMARY KEY,
    kind                          VARCHAR(16)    NOT NULL,
    customer_id                   VARCHAR(50)    NOT NULL REFERENCES customers(id),
    applied_pricing_plan_id       VARCHAR(50)    NOT NULL REFERENCES pricing_plans(id),
    prompt_tokens                 BIGINT         NOT NULL CHECK (prompt_tokens     >= 0),
    completion_tokens             BIGINT         NOT NULL CHECK (completion_tokens >= 0),
    total_tokens                  BIGINT         NOT NULL CHECK (total_tokens      >= 0),
    included_tokens_used          BIGINT         NOT NULL CHECK (included_tokens_used >= 0),
    overage_tokens                BIGINT         NOT NULL CHECK (overage_tokens    >= 0),
    applied_overage_rate_per_1k   DECIMAL(10, 4),
    total_charge                  DECIMAL(10, 2),
    calculated_at                 TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Why CHECK rather than per-state tables: the two cases share most columns
    -- (8 of 11) and are read together for monthly aggregation. Splitting would
    -- force a UNION on every read of "this month's usage" while gaining nothing
    -- the constraints below cannot enforce. See ADR-003.

    CONSTRAINT chk_bill_kind
        CHECK (kind IN ('IN_QUOTA', 'WITH_OVERAGE')),

    -- 総トークン数 = プロンプトトークン数 + 完了トークン数
    CONSTRAINT chk_total_tokens
        CHECK (total_tokens = prompt_tokens + completion_tokens),

    -- 総トークン数 = 枠消費トークン + 超過トークン
    CONSTRAINT chk_token_split
        CHECK (total_tokens = included_tokens_used + overage_tokens),

    -- 枠内請求: no rate, no charge, zero overage; included = total
    CONSTRAINT chk_in_quota_shape
        CHECK (kind <> 'IN_QUOTA' OR (
                overage_tokens              = 0
            AND applied_overage_rate_per_1k IS NULL
            AND total_charge                IS NULL
            AND included_tokens_used        = total_tokens
        )),

    -- 超過込み請求: at least one overage token, rate snapshotted, charge > 0
    CONSTRAINT chk_with_overage_shape
        CHECK (kind <> 'WITH_OVERAGE' OR (
                overage_tokens              >= 1
            AND applied_overage_rate_per_1k IS NOT NULL
            AND total_charge                IS NOT NULL
            AND total_charge                > 0
        ))
);

-- Index supporting the monthly aggregation query
-- (sumTotalTokensInMonth / BillHistoryRepository.findThisMonthTotal).
-- "Last whole UTC month" is the spec-model assumption for month boundaries.
CREATE INDEX idx_bills_customer_calculated_at
    ON bills (customer_id, calculated_at);
