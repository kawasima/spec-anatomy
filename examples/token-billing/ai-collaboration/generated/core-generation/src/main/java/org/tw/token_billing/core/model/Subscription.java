package org.tw.token_billing.core.model;

import java.time.LocalDate;
import java.util.Optional;

/**
 * A customer subscription — the binding of a customer to a pricing plan over
 * an effective period.
 *
 * <p>Corresponds to
 * {@code data 顧客サブスクリプション = サブスクリプションID AND 顧客ID AND 料金プランID AND 有効期間}
 * with {@code data 有効期間 = 開始日 AND 終了日?} in the spec model.
 *
 * <p>The end date is optional: an absent {@code effectiveTo} means the
 * subscription is open-ended. Effective-period containment is computed at the
 * calculation timestamp by {@link #isEffectiveAt(LocalDate)}.
 *
 * @param id           the subscription identifier
 * @param customerId   the subscribed customer
 * @param pricingPlanId the plan being subscribed to
 * @param effectiveFrom the inclusive start date of the subscription
 * @param effectiveTo   the exclusive end date, or empty for open-ended
 */
public record Subscription(
        SubscriptionId id,
        CustomerId customerId,
        PricingPlanId pricingPlanId,
        LocalDate effectiveFrom,
        Optional<LocalDate> effectiveTo
) {

    /**
     * Returns {@code true} if this subscription is in effect on the given date.
     *
     * <p>Containment uses {@code effectiveFrom <= date < effectiveTo} (or no
     * upper bound when {@code effectiveTo} is empty), matching the spec model's
     * comment {@code effective_from <= 計算時点 < effective_to}.
     *
     * @param date the date to test
     * @return whether the subscription is effective on that date
     */
    public boolean isEffectiveAt(LocalDate date) {
        if (date.isBefore(effectiveFrom)) {
            return false;
        }
        return effectiveTo.map(end -> date.isBefore(end)).orElse(true);
    }
}
