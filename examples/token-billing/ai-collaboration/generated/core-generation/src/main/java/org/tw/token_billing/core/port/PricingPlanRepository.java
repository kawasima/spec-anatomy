package org.tw.token_billing.core.port;

import org.tw.token_billing.core.model.PricingPlan;
import org.tw.token_billing.core.model.PricingPlanId;

import java.util.Optional;

/**
 * Read-side port for resolving pricing plans.
 *
 * <p>Used by the Shell layer when implementing
 * {@code behavior 有効な料金プランを取得する}: once an active subscription
 * has been found, its referenced plan is loaded via this port and projected
 * into an {@link org.tw.token_billing.core.model.AppliedPricingPlan}.
 */
public interface PricingPlanRepository {

    /**
     * Finds a plan by id.
     *
     * @param id the plan id
     * @return the plan if it exists, otherwise empty
     */
    Optional<PricingPlan> findById(PricingPlanId id);
}
