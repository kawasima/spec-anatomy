package org.tw.token_billing.core.model;

import java.util.UUID;

/**
 * Typed wrapper for a customer-subscription identifier.
 *
 * <p>Corresponds to {@code data サブスクリプションID = UUID} in the spec model.
 *
 * @param value the underlying UUID
 */
public record SubscriptionId(UUID value) {}
