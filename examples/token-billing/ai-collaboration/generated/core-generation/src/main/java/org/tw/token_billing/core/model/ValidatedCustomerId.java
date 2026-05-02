package org.tw.token_billing.core.model;

/**
 * A {@link CustomerId} that has been verified to exist in the system.
 *
 * <p>Corresponds to {@code data 検証済み顧客ID = 顧客ID (存在検証済み)} in the
 * spec model. The "unverified → verified" mode transition is encoded in the
 * type system: a {@code ValidatedCustomerId} cannot be constructed without
 * having gone through the existence check, so any behavior that requires a
 * verified id refuses to accept the raw {@link CustomerId}.
 *
 * @param value the underlying customer id, guaranteed to refer to an existing customer
 */
public record ValidatedCustomerId(CustomerId value) {}
