package org.tw.token_billing.core.model;

/**
 * The state of a customer's monthly-quota consumption at the calculation time.
 *
 * <p>Corresponds to
 * {@code data 当月の枠消費状況 = 枠未消費 OR 枠一部消費 OR 枠使い切り}
 * (spec model "上位概念B"). Modeling these as three distinct cases — rather
 * than carrying a raw "remaining quota" integer — pushes the
 * "is the quota already used up?" decision into the type system, so the
 * downstream bill calculation can pattern-match exhaustively without
 * scattering integer comparisons across the codebase.
 *
 * <p>Each case exposes the monthly quota and the tokens still available
 * within it (as a {@link TokenAmount}). For {@link Exhausted} the remaining
 * quota is necessarily zero.
 */
public sealed interface MonthlyQuotaUsage
        permits MonthlyQuotaUsage.Untouched,
                MonthlyQuotaUsage.Partial,
                MonthlyQuotaUsage.Exhausted {

    /**
     * The monthly quota for the applied plan in effect at the calculation time.
     *
     * @return the included tokens per calendar month
     */
    TokenAmount monthlyQuota();

    /**
     * The tokens still available within the monthly quota.
     *
     * <p>Equal to {@code monthlyQuota} for {@link Untouched},
     * {@code monthlyQuota - usedThisMonth} for {@link Partial},
     * and zero for {@link Exhausted}.
     *
     * @return the remaining quota as a token amount
     */
    TokenAmount remainingQuota();

    /**
     * No tokens consumed this month yet.
     *
     * <p>Corresponds to {@code data 枠未消費 = 月間込み枠トークン}.
     *
     * @param monthlyQuota the monthly quota
     */
    record Untouched(TokenAmount monthlyQuota) implements MonthlyQuotaUsage {
        @Override
        public TokenAmount remainingQuota() {
            return monthlyQuota;
        }
    }

    /**
     * Some tokens consumed but the quota is not yet exhausted.
     *
     * <p>Corresponds to
     * {@code data 枠一部消費 = 月間込み枠トークン AND 当月使用済みトークン}
     * with the additional constraint {@code 0 < 使用済み < 月間込み枠}.
     *
     * @param monthlyQuota   the monthly quota
     * @param usedThisMonth  the tokens already consumed this month, strictly between zero and the quota
     */
    record Partial(TokenAmount monthlyQuota, TokenAmount usedThisMonth)
            implements MonthlyQuotaUsage {
        public Partial {
            // Why: the "partial" state is meaningless outside the open interval (0, monthlyQuota).
            // Encoding the bounds in the constructor keeps the three cases truly disjoint.
            if (!usedThisMonth.isPositive()) {
                throw new IllegalArgumentException(
                        "Partial requires usedThisMonth > 0; use Untouched for zero usage");
            }
            if (usedThisMonth.value() >= monthlyQuota.value()) {
                throw new IllegalArgumentException(
                        "Partial requires usedThisMonth < monthlyQuota; use Exhausted at or above the quota");
            }
        }

        @Override
        public TokenAmount remainingQuota() {
            return monthlyQuota.minusSaturating(usedThisMonth);
        }
    }

    /**
     * The monthly quota is fully consumed (and possibly already overshot).
     *
     * <p>Corresponds to
     * {@code data 枠使い切り = 月間込み枠トークン AND 当月超過済みトークン}
     * with {@code 当月超過済みトークン >= 月間込み枠}. The "remaining quota"
     * for this state is always zero, matching the spec model comment
     * {@code 枠使い切り: 残枠 = 0}.
     *
     * @param monthlyQuota          the monthly quota
     * @param usedAtOrAboveThisMonth the tokens already consumed this month, at or above the quota
     */
    record Exhausted(TokenAmount monthlyQuota, TokenAmount usedAtOrAboveThisMonth)
            implements MonthlyQuotaUsage {
        public Exhausted {
            if (usedAtOrAboveThisMonth.value() < monthlyQuota.value()) {
                throw new IllegalArgumentException(
                        "Exhausted requires usedAtOrAboveThisMonth >= monthlyQuota; "
                                + "use Partial below the quota");
            }
        }

        @Override
        public TokenAmount remainingQuota() {
            return TokenAmount.ZERO;
        }
    }

    /**
     * Classifies a monthly quota together with an aggregated used-tokens count
     * into the appropriate {@code MonthlyQuotaUsage} case.
     *
     * <p>This is the canonical entry point used by the aggregation behavior in
     * the Shell layer. Keeping the dispatch in one place prevents the three
     * boundary conditions ({@code = 0}, {@code (0, quota)}, {@code >= quota})
     * from leaking into multiple call sites.
     *
     * @param monthlyQuota   the included tokens per calendar month
     * @param usedThisMonth  the aggregated tokens already consumed this month (non-negative)
     * @return the matching {@code MonthlyQuotaUsage} case
     */
    static MonthlyQuotaUsage classify(TokenAmount monthlyQuota, TokenAmount usedThisMonth) {
        if (!usedThisMonth.isPositive()) {
            return new Untouched(monthlyQuota);
        }
        if (usedThisMonth.value() >= monthlyQuota.value()) {
            return new Exhausted(monthlyQuota, usedThisMonth);
        }
        return new Partial(monthlyQuota, usedThisMonth);
    }
}
