package org.tw.token_billing.shell.persistence;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;
import org.tw.token_billing.core.model.Bill;
import org.tw.token_billing.core.model.BillingMonth;
import org.tw.token_billing.core.model.TokenAmount;
import org.tw.token_billing.core.model.ValidatedCustomerId;
import org.tw.token_billing.core.port.BillHistoryRepository;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.ZoneOffset;

/**
 * JdbcClient-backed implementation of {@link BillHistoryRepository}.
 *
 * <p>Two responsibilities, mirroring the port:
 * <ul>
 *   <li>{@link #sumTotalTokensInMonth} — aggregate this-month usage to feed
 *       {@code 当月の枠消費状況を集計する} on the Shell side. The query is a
 *       half-open interval {@code [first day of month, first day of next month)}
 *       in UTC, matching {@link BillingMonth} which is defined as a UTC
 *       {@link java.time.YearMonth}.</li>
 *   <li>{@link #save} — write the bill, switch-dispatching on the sealed
 *       {@link Bill} so that {@link Bill.InQuota} writes NULLs for the
 *       overage rate / charge columns and {@link Bill.WithOverage} writes
 *       both. This is the single point in the codebase where the type split
 *       is projected to columns; the database CHECK constraints catch any
 *       drift.</li>
 * </ul>
 */
@Repository
public class PgBillHistoryRepository implements BillHistoryRepository {

    private final JdbcClient jdbc;

    public PgBillHistoryRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public TokenAmount sumTotalTokensInMonth(ValidatedCustomerId customerId, BillingMonth month) {
        LocalDate firstOfMonth = month.yearMonth().atDay(1);
        LocalDate firstOfNextMonth = firstOfMonth.plusMonths(1);
        Timestamp from = Timestamp.from(firstOfMonth.atStartOfDay().toInstant(ZoneOffset.UTC));
        Timestamp toExclusive = Timestamp.from(firstOfNextMonth.atStartOfDay().toInstant(ZoneOffset.UTC));

        // COALESCE(SUM(...), 0): "no rows" means "no usage yet this month",
        // which the spec model expects to reduce to TokenAmount.ZERO so that
        // 当月の枠消費状況を集計する is total (no failure case for empty history).
        Long total = jdbc.sql("""
                SELECT COALESCE(SUM(total_tokens), 0)
                FROM bills
                WHERE customer_id   = ?
                  AND calculated_at >= ?
                  AND calculated_at <  ?
                """)
                .param(customerId.value().value())
                .param(from)
                .param(toExclusive)
                .query(Long.class)
                .single();
        return new TokenAmount(total == null ? 0L : total);
    }

    @Override
    public void save(Bill bill) {
        // Why a single switch here: the type split lives on the Java side as
        // a sealed interface and on the DB side as a CHECK-constrained
        // column. The Shell is the only layer that has to reconcile the two
        // representations, and the switch is the one place that does it.
        switch (bill) {
            case Bill.InQuota in -> jdbc.sql("""
                    INSERT INTO bills (
                        id, kind, customer_id, applied_pricing_plan_id,
                        prompt_tokens, completion_tokens, total_tokens,
                        included_tokens_used, overage_tokens,
                        applied_overage_rate_per_1k, total_charge,
                        calculated_at
                    ) VALUES (?, 'IN_QUOTA', ?, ?, ?, ?, ?, ?, 0, NULL, NULL, ?)
                    """)
                    .param(in.id().value())
                    .param(in.customerId().value().value())
                    .param(in.appliedPricingPlanId().value())
                    .param(in.promptTokens().value())
                    .param(in.completionTokens().value())
                    .param(in.totalTokens().value())
                    .param(in.quotaConsumedTokens().value())
                    .param(Timestamp.from(in.calculatedAt()))
                    .update();

            case Bill.WithOverage wo -> jdbc.sql("""
                    INSERT INTO bills (
                        id, kind, customer_id, applied_pricing_plan_id,
                        prompt_tokens, completion_tokens, total_tokens,
                        included_tokens_used, overage_tokens,
                        applied_overage_rate_per_1k, total_charge,
                        calculated_at
                    ) VALUES (?, 'WITH_OVERAGE', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """)
                    .param(wo.id().value())
                    .param(wo.customerId().value().value())
                    .param(wo.appliedPricingPlanId().value())
                    .param(wo.promptTokens().value())
                    .param(wo.completionTokens().value())
                    .param(wo.totalTokens().value())
                    .param(wo.quotaConsumedTokens().value())
                    .param(wo.overageTokens().value())
                    .param(wo.appliedOverageRatePer1K().amount())
                    .param(wo.totalCharge().amount())
                    .param(Timestamp.from(wo.calculatedAt()))
                    .update();
        }
    }
}
