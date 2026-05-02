package org.tw.token_billing.core.behavior;

import org.tw.token_billing.core.model.AppliedPricingPlan;
import org.tw.token_billing.core.model.Bill;
import org.tw.token_billing.core.model.BillId;
import org.tw.token_billing.core.model.Money;
import org.tw.token_billing.core.model.MonthlyQuotaUsage;
import org.tw.token_billing.core.model.OverageTokens;
import org.tw.token_billing.core.model.TokenAmount;
import org.tw.token_billing.core.model.ValidatedUsageReport;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * Pure bill-calculation behavior.
 *
 * <p>Implements the spec-model behavior
 * <pre>
 * behavior 請求を計算する =
 *     検証済み使用申告
 *     AND 当月の枠消費状況
 *     AND 適用料金プラン
 *     AND 計算時点
 *     -> 枠内請求 OR 超過込み請求
 * </pre>
 *
 * <p>Inputs are restricted to the validated / projected types:
 * <ul>
 *   <li>{@link ValidatedUsageReport} guarantees a verified customer id and
 *       non-negative token counts.</li>
 *   <li>{@link MonthlyQuotaUsage} encodes the three quota states as distinct
 *       cases, so the calculation never has to do raw integer comparisons on
 *       a "remaining quota" number.</li>
 *   <li>{@link AppliedPricingPlan} is the plan projection containing only
 *       what the calculation needs (id, monthly quota, overage rate),
 *       eliminating stamp coupling against the full {@code PricingPlan} or
 *       the customer subscription record.</li>
 * </ul>
 *
 * <p>Because every input is already validated or pre-confirmed, this behavior
 * is total — it always returns a {@link Bill}, never an error.
 */
public final class BillCalculationBehavior {

    /** Number of tokens that one unit of the overage rate covers. */
    private static final BigDecimal TOKENS_PER_RATE_UNIT = BigDecimal.valueOf(1000);

    private BillCalculationBehavior() {}

    /**
     * Calculates a bill for a single validated usage report.
     *
     * <p>Why "consume the quota first": the spec model captures the README
     * rule "Included tokens first: consume monthly quota before charging
     * overage" — the customer-friendly direction (use the promised free
     * allowance before billing). Returning a {@link Bill.InQuota} or
     * {@link Bill.WithOverage} based on whether overage actually exists keeps
     * the case distinction in the type system rather than in flag-checking
     * code downstream.
     *
     * @param report      the validated usage report
     * @param quotaUsage  the customer's monthly quota state at calculation time
     * @param plan        the projected plan (provides quota size and overage rate)
     * @param calculatedAt the calculation timestamp
     * @return the calculated bill (in-quota or with-overage)
     */
    public static Bill calculate(
            ValidatedUsageReport report,
            MonthlyQuotaUsage quotaUsage,
            AppliedPricingPlan plan,
            Instant calculatedAt
    ) {
        TokenAmount total = report.totalTokens();
        TokenAmount remaining = quotaUsage.remainingQuota();

        // 「枠を先に消費する」: 枠消費 = min(申告総, 残枠)
        TokenAmount quotaConsumed = total.min(remaining);
        long overageValue = total.value() - quotaConsumed.value();

        BillId billId = new BillId(UUID.randomUUID());

        if (overageValue == 0) {
            // 結果が枠内に収まる: 超過関連フィールドを持たない型を返す
            return new Bill.InQuota(
                    billId,
                    report.customerId(),
                    plan.id(),
                    report.promptTokens(),
                    report.completionTokens(),
                    calculatedAt
            );
        }

        OverageTokens overage = new OverageTokens(overageValue);
        Money charge = computeOverageCharge(overage, plan.overageRatePer1K());

        return new Bill.WithOverage(
                billId,
                report.customerId(),
                plan.id(),
                report.promptTokens(),
                report.completionTokens(),
                quotaConsumed,
                overage,
                plan.overageRatePer1K(),
                charge,
                calculatedAt
        );
    }

    /**
     * Computes the overage charge as
     * {@code round_half_up( (超過トークン / 1000) * 適用超過レート, 2 )}.
     *
     * <p>The rate is denominated per 1000 tokens, so we scale the multiplier
     * before applying the rate. {@link Money#timesRoundedHalfUp(BigDecimal)}
     * applies the spec-model rounding rule (HALF_UP to two decimals).
     *
     * @param overage the overage tokens (at least one, by type)
     * @param ratePer1K the per-1000-token overage rate
     * @return the charge as money
     */
    private static Money computeOverageCharge(OverageTokens overage, Money ratePer1K) {
        BigDecimal multiplier = BigDecimal.valueOf(overage.value())
                .divide(TOKENS_PER_RATE_UNIT, 10, java.math.RoundingMode.HALF_UP);
        return ratePer1K.timesRoundedHalfUp(multiplier);
    }
}
