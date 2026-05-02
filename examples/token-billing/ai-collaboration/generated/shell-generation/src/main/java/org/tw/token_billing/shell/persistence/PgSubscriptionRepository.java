package org.tw.token_billing.shell.persistence;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;
import org.tw.token_billing.core.model.Subscription;
import org.tw.token_billing.core.model.ValidatedCustomerId;
import org.tw.token_billing.core.port.SubscriptionRepository;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.tw.token_billing.shell.persistence.MapBillDecoders.SUBSCRIPTION_ROW;

/**
 * JdbcClient-backed implementation of the Core's {@link SubscriptionRepository}.
 *
 * <p>Implements the spec-model rule
 * {@code effective_from <= 計算時点 < effective_to (or effective_to IS NULL)}.
 * The calculation timestamp is converted to a {@link LocalDate} in UTC for
 * the comparison — matching the spec model's stated month-boundary
 * assumption (UTC calendar dates).
 */
@Repository
public class PgSubscriptionRepository implements SubscriptionRepository {

    private final JdbcClient jdbc;

    public PgSubscriptionRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public Optional<Subscription> findActive(ValidatedCustomerId customerId, Instant at) {
        LocalDate atDate = at.atOffset(ZoneOffset.UTC).toLocalDate();
        // Why ORDER BY effective_from DESC LIMIT 1: the spec model presumes a
        // single active subscription per customer, but does not exclude data
        // anomalies. Picking the latest-starting active row is the safest
        // policy and keeps the read deterministic.
        List<Map<String, Object>> rows = jdbc.sql("""
                SELECT id, customer_id, plan_id, effective_from, effective_to
                FROM customer_subscriptions
                WHERE customer_id = ?
                  AND effective_from <= ?
                  AND (effective_to IS NULL OR effective_to > ?)
                ORDER BY effective_from DESC
                LIMIT 1
                """)
                .param(customerId.value().value())
                .param(java.sql.Date.valueOf(atDate))
                .param(java.sql.Date.valueOf(atDate))
                .query()
                .listOfRows();
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(SUBSCRIPTION_ROW.decode(rows.getFirst()).getOrThrow());
    }
}
