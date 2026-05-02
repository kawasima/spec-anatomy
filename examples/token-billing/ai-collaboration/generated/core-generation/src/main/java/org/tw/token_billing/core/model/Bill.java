package org.tw.token_billing.core.model;

import java.time.Instant;

/**
 * The result of calculating a bill for a single usage report.
 *
 * <p>Corresponds to {@code data 請求 = 枠内請求 OR 超過込み請求}
 * (spec model "上位概念A"). The two cases are kept structurally distinct:
 * <ul>
 *   <li>{@link InQuota} — the request fit within the remaining monthly quota.
 *       No charge is owed, and the type therefore does not carry an overage
 *       count, an applied overage rate, or a charge amount.</li>
 *   <li>{@link WithOverage} — the request exceeded the remaining quota. The
 *       overage portion is at least one token, the applied overage rate is
 *       snapshotted from the pricing plan at calculation time, and the charge
 *       amount is strictly positive.</li>
 * </ul>
 *
 * <p>This split avoids the "{@code overageTokens = 0} sentinel" anti-pattern.
 * Downstream consumers (storage, reporting, accounting) match on the case
 * rather than checking integer zero.
 */
public sealed interface Bill permits Bill.InQuota, Bill.WithOverage {

    /** @return the bill identifier */
    BillId id();

    /** @return the verified customer this bill belongs to */
    ValidatedCustomerId customerId();

    /** @return the plan that was applied at calculation time */
    PricingPlanId appliedPricingPlanId();

    /** @return the prompt tokens declared in the source usage report */
    TokenAmount promptTokens();

    /** @return the completion tokens declared in the source usage report */
    TokenAmount completionTokens();

    /**
     * @return the total tokens for this bill
     *         ({@code 総トークン数 = プロンプトトークン数 + 完了トークン数})
     */
    TokenAmount totalTokens();

    /** @return the portion of the total tokens that was billed against the monthly quota */
    TokenAmount quotaConsumedTokens();

    /** @return the timestamp at which this bill was calculated */
    Instant calculatedAt();

    /**
     * A bill whose total fit entirely within the remaining monthly quota.
     *
     * <p>Corresponds to
     * <pre>
     * data 枠内請求 = 請求ID
     *           AND 検証済み顧客ID
     *           AND 適用料金プランID
     *           AND プロンプトトークン数 AND 完了トークン数
     *           AND 総トークン数
     *           AND 枠消費トークン   // = 総トークン数
     *           AND 計算日時
     * </pre>
     *
     * <p>Why no charge / overage / rate: the spec model notes that an in-quota
     * bill is "売上0" and that carrying zero columns ("0円", "0トークン超過")
     * would force every downstream aggregation to re-decide whether overage
     * was actually charged. The structural split makes that decision
     * impossible to forget.
     *
     * @param id                   the bill identifier
     * @param customerId           the verified customer
     * @param appliedPricingPlanId the plan in effect at calculation time
     * @param promptTokens         the prompt tokens from the report
     * @param completionTokens     the completion tokens from the report
     * @param calculatedAt         the calculation timestamp
     */
    record InQuota(
            BillId id,
            ValidatedCustomerId customerId,
            PricingPlanId appliedPricingPlanId,
            TokenAmount promptTokens,
            TokenAmount completionTokens,
            Instant calculatedAt
    ) implements Bill {

        @Override
        public TokenAmount totalTokens() {
            return promptTokens.plus(completionTokens);
        }

        /**
         * For an in-quota bill, the quota-consumed tokens are exactly the
         * total tokens (the spec model invariant
         * {@code 枠消費トークン(b) = 総トークン数(b)}).
         */
        @Override
        public TokenAmount quotaConsumedTokens() {
            return totalTokens();
        }
    }

    /**
     * A bill whose total exceeded the remaining monthly quota and therefore
     * incurs a charge.
     *
     * <p>Corresponds to
     * <pre>
     * data 超過込み請求 = 請求ID
     *               AND 検証済み顧客ID
     *               AND 適用料金プランID
     *               AND プロンプトトークン数 AND 完了トークン数
     *               AND 総トークン数
     *               AND 枠消費トークン        // 0以上
     *               AND 超過トークン          // 1以上 (型保証)
     *               AND 適用超過レート        // 料金プランからのスナップショット
     *               AND 請求金額              // 0より大きい (型保証)
     *               AND 計算日時
     * </pre>
     *
     * <p>The applied overage rate is snapshotted at the calculation time so
     * that later changes to the pricing plan do not retroactively alter the
     * meaning of historical bills.
     *
     * @param id                       the bill identifier
     * @param customerId               the verified customer
     * @param appliedPricingPlanId     the plan in effect at calculation time
     * @param promptTokens             the prompt tokens from the report
     * @param completionTokens         the completion tokens from the report
     * @param quotaConsumedTokens      the portion billed against the monthly quota (may be zero)
     * @param overageTokens            the portion billed at the overage rate (at least one)
     * @param appliedOverageRatePer1K  the per-1000-token rate snapshotted from the plan
     * @param totalCharge              the calculated charge, strictly greater than zero
     * @param calculatedAt             the calculation timestamp
     */
    record WithOverage(
            BillId id,
            ValidatedCustomerId customerId,
            PricingPlanId appliedPricingPlanId,
            TokenAmount promptTokens,
            TokenAmount completionTokens,
            TokenAmount quotaConsumedTokens,
            OverageTokens overageTokens,
            Money appliedOverageRatePer1K,
            Money totalCharge,
            Instant calculatedAt
    ) implements Bill {

        public WithOverage {
            // Why: the spec model invariants
            //   総トークン数 = 枠消費トークン + 超過トークン
            //   請求金額 > 0
            // are enforceable here at construction so that no malformed
            // WithOverage can be serialized or persisted.
            if (!totalCharge.isPositive()) {
                throw new IllegalArgumentException(
                        "WithOverage requires totalCharge > 0; use InQuota for zero charge");
            }
        }

        @Override
        public TokenAmount totalTokens() {
            return quotaConsumedTokens.plus(overageTokens.asTokenAmount());
        }
    }
}
