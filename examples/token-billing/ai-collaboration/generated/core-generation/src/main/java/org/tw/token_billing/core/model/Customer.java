package org.tw.token_billing.core.model;

/**
 * A registered customer.
 *
 * <p>Corresponds to {@code data 顧客 = 顧客ID AND 顧客名} in the spec model.
 *
 * @param id   the customer identifier
 * @param name the customer's display name
 */
public record Customer(CustomerId id, String name) {}
