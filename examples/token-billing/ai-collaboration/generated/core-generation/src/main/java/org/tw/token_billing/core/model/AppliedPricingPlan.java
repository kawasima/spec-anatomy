package org.tw.token_billing.core.model;

/**
 * The projection of {@link PricingPlan} that bill calculation actually needs.
 *
 * <p>Corresponds to
 * {@code data 適用料金プラン = 料金プランID AND 月間込み枠トークン AND 超過レート}
 * in the spec model. Defined as a separate type to eliminate stamp coupling
 * (the plan name is irrelevant to the calculation, and a customer
 * subscription's effective period is irrelevant once the plan has been
 * resolved at a calculation timestamp).
 *
 * @param id               the source plan identifier (preserved for the bill record)
 * @param monthlyQuota     the included tokens per calendar month
 * @param overageRatePer1K the price applied per 1000 overage tokens at this calculation time
 */
public record AppliedPricingPlan(
        PricingPlanId id,
        TokenAmount monthlyQuota,
        Money overageRatePer1K
) {

    /**
     * Projects a full {@link PricingPlan} down to its calculation-relevant fields.
     *
     * @param plan the source pricing plan
     * @return the projection used by the bill calculation behavior
     */
    public static AppliedPricingPlan from(PricingPlan plan) {
        return new AppliedPricingPlan(plan.id(), plan.monthlyQuota(), plan.overageRatePer1K());
    }
}
