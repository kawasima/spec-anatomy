package org.tw.token_billing.shell.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.tw.token_billing.core.port.Clock;

import java.time.Instant;

/**
 * Wires the Core's {@link Clock} port to a real wall-clock implementation.
 *
 * <p>Externalising "now" through a port keeps the Core deterministic and
 * lets spec tests (and the in-process tests for this Shell) supply a fixed
 * instant via a different bean definition without touching production code.
 */
@Configuration
public class ClockConfig {

    /**
     * Wall-clock implementation backed by {@link Instant#now()}.
     *
     * @return the production clock
     */
    @Bean
    public Clock systemClock() {
        return Instant::now;
    }
}
