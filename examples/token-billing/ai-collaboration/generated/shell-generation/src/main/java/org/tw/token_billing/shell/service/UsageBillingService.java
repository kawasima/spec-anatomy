package org.tw.token_billing.shell.service;

import org.springframework.stereotype.Service;
import org.tw.token_billing.core.behavior.BillCalculationBehavior;
import org.tw.token_billing.core.model.AppliedPricingPlan;
import org.tw.token_billing.core.model.Bill;
import org.tw.token_billing.core.model.BillingMonth;
import org.tw.token_billing.core.model.MonthlyQuotaUsage;
import org.tw.token_billing.core.model.PricingPlan;
import org.tw.token_billing.core.model.Subscription;
import org.tw.token_billing.core.model.TokenAmount;
import org.tw.token_billing.core.model.ValidatedCustomerId;
import org.tw.token_billing.core.model.ValidatedUsageReport;
import org.tw.token_billing.core.port.BillHistoryRepository;
import org.tw.token_billing.core.port.Clock;
import org.tw.token_billing.core.port.CustomerRepository;
import org.tw.token_billing.core.port.PricingPlanRepository;
import org.tw.token_billing.core.port.SubscriptionRepository;
import org.tw.token_billing.shell.api.JsonUsageDecoders.UsageReportCommand;

import java.time.Instant;
import java.util.Optional;

/**
 * Orchestrates the spec-model workflow
 * {@code 使用申告から請求を生成する} on top of the Core ports.
 *
 * <p>The Core calls out the workflow steps explicitly:
 * <ol>
 *   <li>トークン数を検証する — already done at the JSON boundary
 *       ({@code TokenAmount} value-type constructor + Raoh
 *       {@code nonNegative()})</li>
 *   <li>顧客IDを検証する — {@link CustomerRepository#findById}</li>
 *   <li>有効な料金プランを取得する — {@link SubscriptionRepository#findActive}
 *       then {@link PricingPlanRepository#findById}, projected to
 *       {@link AppliedPricingPlan}</li>
 *   <li>当月の枠消費状況を集計する — {@link BillHistoryRepository#sumTotalTokensInMonth}
 *       fed into {@link MonthlyQuotaUsage#classify}</li>
 *   <li>請求を計算する — {@link BillCalculationBehavior#calculate}</li>
 * </ol>
 *
 * <p>Failures are returned as a {@link Result} sealed type rather than
 * thrown, so the controller can pattern-match exhaustively on each
 * spec-model failure case and pick the right HTTP status.
 */
@Service
public class UsageBillingService {

    private final CustomerRepository customers;
    private final SubscriptionRepository subscriptions;
    private final PricingPlanRepository plans;
    private final BillHistoryRepository bills;
    private final Clock clock;

    public UsageBillingService(
            CustomerRepository customers,
            SubscriptionRepository subscriptions,
            PricingPlanRepository plans,
            BillHistoryRepository bills,
            Clock clock
    ) {
        this.customers     = customers;
        this.subscriptions = subscriptions;
        this.plans         = plans;
        this.bills         = bills;
        this.clock         = clock;
    }

    /**
     * Runs the workflow for a decoded {@link UsageReportCommand}.
     *
     * @param command the decoded request
     * @return a {@link Result} that carries either the calculated {@link Bill}
     *         or the specific business failure case
     */
    public Result process(UsageReportCommand command) {
        Instant now = clock.now();

        // Step 1: customer existence check (AC1)
        var customer = customers.findById(command.customerId());
        if (customer.isEmpty()) {
            return new Result.CustomerNotFound(command.customerId().value());
        }
        ValidatedCustomerId validated = new ValidatedCustomerId(command.customerId());

        // Step 2: active subscription + plan projection
        Optional<Subscription> active = subscriptions.findActive(validated, now);
        if (active.isEmpty()) {
            return new Result.SubscriptionInactive(command.customerId().value());
        }
        Optional<PricingPlan> plan = plans.findById(active.get().pricingPlanId());
        if (plan.isEmpty()) {
            // Why this is a 500 / internal error rather than a domain failure:
            // a subscription pointing at a non-existent plan is a referential
            // integrity violation. The DB FK already prevents it; reaching
            // this branch means the data model is broken, not the request.
            return new Result.DataIntegrityIssue(
                    "subscription %s references missing pricing plan %s"
                            .formatted(active.get().id().value(), active.get().pricingPlanId().value()));
        }
        AppliedPricingPlan applied = AppliedPricingPlan.from(plan.get());

        // Step 3: aggregate this month's usage and classify into the 3-state
        //         枠消費状況. The BillingMonth is derived from `now` in UTC,
        //         matching the spec model's stated assumption.
        BillingMonth month = BillingMonth.of(now);
        TokenAmount usedThisMonth = bills.sumTotalTokensInMonth(validated, month);
        MonthlyQuotaUsage quotaUsage = MonthlyQuotaUsage.classify(applied.monthlyQuota(), usedThisMonth);

        // Step 4: pure calculation in the Core
        ValidatedUsageReport report = new ValidatedUsageReport(
                validated, command.promptTokens(), command.completionTokens());
        Bill bill = BillCalculationBehavior.calculate(report, quotaUsage, applied, now);

        // Step 5: persist
        bills.save(bill);

        return new Result.Calculated(bill);
    }

    /**
     * Sealed result of the workflow. Each case is exactly one of the
     * spec-model outcomes, plus a {@link DataIntegrityIssue} for the
     * "should not happen but isn't a domain error" branch.
     */
    public sealed interface Result
            permits Result.Calculated,
                    Result.CustomerNotFound,
                    Result.SubscriptionInactive,
                    Result.DataIntegrityIssue {

        /** Successful calculation — carries the {@link Bill} in either of its two cases. */
        record Calculated(Bill bill) implements Result {}

        /** Spec model {@code 顧客未登録エラー}. */
        record CustomerNotFound(String customerId) implements Result {}

        /** Spec model {@code サブスクリプション無効エラー}. */
        record SubscriptionInactive(String customerId) implements Result {}

        /** Internal data-integrity issue (FK should have prevented it). */
        record DataIntegrityIssue(String detail) implements Result {}
    }
}
