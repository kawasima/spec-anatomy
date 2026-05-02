package org.tw.token_billing.core.model;

/**
 * The overage portion of a billing report — strictly at least one token.
 *
 * <p>Corresponds to {@code data 超過トークン = 1以上の整数} in the spec model.
 * The "must be at least one" invariant is what distinguishes this type from
 * {@link TokenAmount}: a {@link Bill.WithOverage} cannot exist without overage,
 * and modelling that as a separate type (rather than {@code TokenAmount} plus a
 * runtime check) makes "no-overage" bills structurally impossible to confuse
 * with "with-overage" bills.
 *
 * <p>The constructor enforces the {@code value >= 1} invariant.
 *
 * @param value the overage count, guaranteed to be at least one
 */
public record OverageTokens(long value) {

    public OverageTokens {
        if (value < 1) {
            throw new IllegalArgumentException("overage tokens must be at least 1: " + value);
        }
    }

    /**
     * Returns the underlying count as a {@link TokenAmount}.
     *
     * @return the same count, viewed as a non-negative {@code TokenAmount}
     */
    public TokenAmount asTokenAmount() {
        return new TokenAmount(value);
    }
}
