package org.tw.token_billing.core.model;

import java.util.UUID;

/**
 * Typed wrapper for a bill identifier.
 *
 * <p>Corresponds to {@code data 請求ID = UUID} in the spec model.
 *
 * @param value the underlying UUID
 */
public record BillId(UUID value) {}
