package org.tw.token_billing.core.model;

import java.time.Instant;
import java.time.YearMonth;
import java.time.ZoneOffset;

/**
 * The calendar month a bill belongs to, used for monthly-quota accounting.
 *
 * <p>The spec model leaves the month-boundary definition as a "推測" (presumed)
 * — it is interpreted here as the UTC calendar month, matching the spec
 * model's comment {@code 推測: UTC暦月}. Shell-side persistence and queries
 * can rebase to a different timezone if a future requirement clarifies it,
 * but the Core honours the documented assumption.
 *
 * @param yearMonth the year-and-month, in UTC
 */
public record BillingMonth(YearMonth yearMonth) {

    /**
     * Returns the billing month containing the given calculation timestamp,
     * interpreted in UTC.
     *
     * @param at the calculation timestamp
     * @return the corresponding billing month
     */
    public static BillingMonth of(Instant at) {
        return new BillingMonth(YearMonth.from(at.atOffset(ZoneOffset.UTC)));
    }
}
