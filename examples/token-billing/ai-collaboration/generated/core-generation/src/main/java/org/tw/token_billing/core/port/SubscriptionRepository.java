package org.tw.token_billing.core.port;

import org.tw.token_billing.core.model.Subscription;
import org.tw.token_billing.core.model.ValidatedCustomerId;

import java.time.Instant;
import java.util.Optional;

/**
 * Read-side port for resolving a customer's subscription at a calculation time.
 *
 * <p>Used by the Shell-layer implementation of
 * {@code behavior 有効な料金プランを取得する}, which reads the active
 * subscription and then resolves the corresponding pricing plan via
 * {@link PricingPlanRepository}.
 */
public interface SubscriptionRepository {

    /**
     * Returns the customer's subscription that is in effect at the given
     * timestamp, if any.
     *
     * <p>"In effect" matches
     * {@code effective_from <= at < effective_to (or effective_to IS NULL)}
     * from the spec model.
     *
     * @param customerId the verified customer id
     * @param at         the calculation timestamp
     * @return the active subscription, or empty if none
     */
    Optional<Subscription> findActive(ValidatedCustomerId customerId, Instant at);
}
