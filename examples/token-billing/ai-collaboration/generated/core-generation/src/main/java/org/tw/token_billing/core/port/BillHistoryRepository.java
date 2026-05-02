package org.tw.token_billing.core.port;

import org.tw.token_billing.core.model.Bill;
import org.tw.token_billing.core.model.BillingMonth;
import org.tw.token_billing.core.model.TokenAmount;
import org.tw.token_billing.core.model.ValidatedCustomerId;

/**
 * Bill-history persistence port.
 *
 * <p>Provides two responsibilities used by the workflow:
 * <ul>
 *   <li>{@link #sumTotalTokensInMonth} — feeds
 *       {@code behavior 当月の枠消費状況を集計する} on the Shell side.
 *       Returning {@link TokenAmount#ZERO ZERO} for an empty history is
 *       what makes the aggregation behavior total.</li>
 *   <li>{@link #save} — persists either {@link Bill.InQuota} or
 *       {@link Bill.WithOverage}; the Shell implementation matches on the
 *       sealed-interface case to write the appropriate columns.</li>
 * </ul>
 */
public interface BillHistoryRepository {

    /**
     * Sums the {@code total_tokens} of all bills already calculated for the
     * given customer in the given billing month.
     *
     * <p>For an empty history the implementation must return
     * {@link TokenAmount#ZERO}.
     *
     * @param customerId the verified customer id
     * @param month      the billing month
     * @return the aggregated token usage so far this month
     */
    TokenAmount sumTotalTokensInMonth(ValidatedCustomerId customerId, BillingMonth month);

    /**
     * Persists a calculated bill.
     *
     * @param bill the bill to save
     */
    void save(Bill bill);
}
