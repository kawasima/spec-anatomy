package org.tw.token_billing.shell;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the token-billing Shell application.
 *
 * <p>The {@code shell} package owns Spring wiring (controllers, repositories,
 * configuration); the {@code core} package — which lives under
 * {@code org.tw.token_billing.core} — is intentionally excluded from
 * Spring component scanning by virtue of being above the
 * {@link SpringBootApplication}'s base package. The Core stays a plain
 * Java library with no Spring annotations.
 */
@SpringBootApplication
public class TokenBillingApplication {

    public static void main(String[] args) {
        SpringApplication.run(TokenBillingApplication.class, args);
    }
}
