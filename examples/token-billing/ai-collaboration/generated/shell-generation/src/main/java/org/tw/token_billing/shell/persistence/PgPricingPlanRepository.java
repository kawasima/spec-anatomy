package org.tw.token_billing.shell.persistence;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;
import org.tw.token_billing.core.model.PricingPlan;
import org.tw.token_billing.core.model.PricingPlanId;
import org.tw.token_billing.core.port.PricingPlanRepository;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.tw.token_billing.shell.persistence.MapBillDecoders.PRICING_PLAN_ROW;

/**
 * JdbcClient-backed implementation of the Core's {@link PricingPlanRepository}.
 *
 * <p>Returns the full {@link PricingPlan} resource. The Shell-side service
 * narrows it to the Core's {@code AppliedPricingPlan} projection at the call
 * site (see {@code UsageBillingService}) so that the persistence layer does
 * not depend on the projection type.
 */
@Repository
public class PgPricingPlanRepository implements PricingPlanRepository {

    private final JdbcClient jdbc;

    public PgPricingPlanRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public Optional<PricingPlan> findById(PricingPlanId id) {
        List<Map<String, Object>> rows = jdbc
                .sql("SELECT id, name, monthly_quota, overage_rate_per_1k FROM pricing_plans WHERE id = ?")
                .param(id.value())
                .query()
                .listOfRows();
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(PRICING_PLAN_ROW.decode(rows.getFirst()).getOrThrow());
    }
}
