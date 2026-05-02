package org.tw.token_billing.core.port;

import java.time.Instant;

/**
 * Calculation-time provider, abstracted so the Shell can supply a real clock
 * in production and a fixed instant in spec tests.
 *
 * <p>The spec model treats {@code 計算時点} (the calculation timestamp) as a
 * first-class input to several behaviors — subscription resolution, monthly
 * usage aggregation, and the bill itself. Externalising it through this port
 * keeps the Core deterministic and testable.
 */
public interface Clock {

    /**
     * Returns the current calculation instant.
     *
     * @return the current instant
     */
    Instant now();
}
