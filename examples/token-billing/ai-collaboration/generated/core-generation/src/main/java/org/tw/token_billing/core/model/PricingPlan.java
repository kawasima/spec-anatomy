package org.tw.token_billing.core.model;

/**
 * A reusable pricing plan that customers subscribe to.
 *
 * <p>Corresponds to
 * {@code data 料金プラン = 料金プランID AND 料金プラン名 AND 月間込み枠トークン AND 超過レート}
 * in the spec model.
 *
 * <p>This is the full resource. For per-bill calculation, the plan is projected
 * down to {@link AppliedPricingPlan}, which excludes fields the calculation does
 * not need (the plan name) — see "上位概念D" in the spec model (stamp-coupling
 * elimination).
 *
 * @param id              the plan identifier
 * @param name            the plan's display name
 * @param monthlyQuota    the included tokens per calendar month
 * @param overageRatePer1K the price applied per 1000 overage tokens
 */
public record PricingPlan(
        PricingPlanId id,
        String name,
        TokenAmount monthlyQuota,
        Money overageRatePer1K
) {}
