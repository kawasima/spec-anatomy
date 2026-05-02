package org.tw.token_billing.core.model;

/**
 * Typed wrapper for a pricing plan identifier.
 *
 * <p>Corresponds to {@code data 料金プランID = 文字列} in the spec model.
 *
 * @param value the underlying identifier string
 */
public record PricingPlanId(String value) {}
