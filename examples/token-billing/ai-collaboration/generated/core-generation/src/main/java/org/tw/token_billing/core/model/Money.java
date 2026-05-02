package org.tw.token_billing.core.model;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Currency;

/**
 * A monetary amount with currency.
 *
 * <p>Used both for the per-1000-token overage rate ({@code data 超過レート}) and
 * for the calculated charge on an overage bill ({@code data 請求金額}).
 *
 * <p>The spec model leaves currency and rounding rules under "推測" (presumed):
 * we encode the currency on the value (defaulting to USD via
 * {@link #usd(BigDecimal)}) and provide a multiply-and-round helper that uses
 * {@link RoundingMode#HALF_UP HALF_UP} to two decimal places, matching the
 * spec model's stated assumption.
 *
 * @param amount   the monetary amount, scale-preserved
 * @param currency the currency
 */
public record Money(BigDecimal amount, Currency currency) {

    /** USD, the assumed currency for this domain (per spec model 推測). */
    public static final Currency USD = Currency.getInstance("USD");

    public Money {
        if (amount == null) {
            throw new IllegalArgumentException("amount must not be null");
        }
        if (currency == null) {
            throw new IllegalArgumentException("currency must not be null");
        }
        if (amount.signum() < 0) {
            throw new IllegalArgumentException("amount must be non-negative: " + amount);
        }
    }

    /**
     * Constructs a USD amount.
     *
     * @param amount the amount in USD
     * @return a USD-denominated {@code Money}
     */
    public static Money usd(BigDecimal amount) {
        return new Money(amount, USD);
    }

    /**
     * Returns this amount multiplied by a non-negative scalar, rounded
     * half-up to two decimal places.
     *
     * <p>This is the rounding rule used for the overage charge calculation:
     * {@code 請求金額 = round_half_up( (超過トークン / 1000) * 適用超過レート, 2 )}.
     *
     * @param multiplier the scalar to multiply by
     * @return the rounded product as {@code Money}, with the same currency
     */
    public Money timesRoundedHalfUp(BigDecimal multiplier) {
        BigDecimal product = amount.multiply(multiplier).setScale(2, RoundingMode.HALF_UP);
        return new Money(product, currency);
    }

    /**
     * Returns {@code true} if this amount is strictly greater than zero.
     *
     * @return {@code true} when amount &gt; 0
     */
    public boolean isPositive() {
        return amount.signum() > 0;
    }
}
