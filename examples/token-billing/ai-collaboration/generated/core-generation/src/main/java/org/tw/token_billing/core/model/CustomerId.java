package org.tw.token_billing.core.model;

/**
 * Typed wrapper for a customer identifier (raw, not yet validated).
 *
 * <p>Corresponds to {@code data 顧客ID = 文字列} in the spec model.
 * A {@code CustomerId} that has been confirmed to exist in the system is
 * promoted to {@link ValidatedCustomerId} at the boundary.
 *
 * @param value the underlying identifier string
 */
public record CustomerId(String value) {}
