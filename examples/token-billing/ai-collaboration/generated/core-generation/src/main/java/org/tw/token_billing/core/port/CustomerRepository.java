package org.tw.token_billing.core.port;

import org.tw.token_billing.core.model.Customer;
import org.tw.token_billing.core.model.CustomerId;

import java.util.Optional;

/**
 * Read-side port for customer existence checks.
 *
 * <p>The Core only needs to know whether a {@link CustomerId} refers to an
 * existing {@link Customer}; the spec model's
 * {@code behavior 顧客IDを検証する} is implemented at the Shell layer using
 * this port to confirm the existence and then promote the id to a
 * {@link org.tw.token_billing.core.model.ValidatedCustomerId}.
 *
 * <p>The Shell provides the implementation; this interface intentionally
 * carries no Spring annotations.
 */
public interface CustomerRepository {

    /**
     * Finds a customer by id.
     *
     * @param id the customer id to look up
     * @return the customer if it exists, otherwise empty
     */
    Optional<Customer> findById(CustomerId id);
}
