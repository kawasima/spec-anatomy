package org.tw.token_billing.core.model;

/**
 * A non-negative count of tokens.
 *
 * <p>Used for monthly quotas, per-report token counts, accumulated usage, and
 * billed quota/overage portions. The spec model expresses several of these as
 * distinct {@code data 非負整数} types ({@code 月間込み枠トークン},
 * {@code プロンプトトークン数}, {@code 完了トークン数}, {@code 総トークン数},
 * {@code 枠消費トークン}); they share the same shape so we represent them with
 * a single value type at the Java level. Stronger invariants such as
 * "must be at least one" are encoded via separate types
 * ({@link OverageTokens}, {@link MonthlyQuotaUsage.Partial}, etc).
 *
 * <p>The constructor enforces non-negativity. Construct from the boundary
 * via decoders, not from arbitrary integers in domain code.
 *
 * @param value the underlying non-negative count
 */
public record TokenAmount(long value) {

    /** A {@code TokenAmount} of zero, useful as an additive identity. */
    public static final TokenAmount ZERO = new TokenAmount(0);

    public TokenAmount {
        if (value < 0) {
            throw new IllegalArgumentException("token amount must be non-negative: " + value);
        }
    }

    /**
     * Returns this amount plus the other, never overflowing into negatives.
     *
     * @param other the other amount to add
     * @return a new {@code TokenAmount} whose value is the sum
     */
    public TokenAmount plus(TokenAmount other) {
        return new TokenAmount(this.value + other.value);
    }

    /**
     * Returns the saturating subtraction {@code max(0, this - other)}.
     *
     * <p>Used to compute remaining quota from a known monthly quota and an
     * accumulated usage that may exceed it.
     *
     * @param other the amount to subtract
     * @return a new {@code TokenAmount} that is at least zero
     */
    public TokenAmount minusSaturating(TokenAmount other) {
        long diff = this.value - other.value;
        return diff <= 0 ? ZERO : new TokenAmount(diff);
    }

    /**
     * Returns the smaller of this and the other.
     *
     * @param other the other amount
     * @return the smaller of the two
     */
    public TokenAmount min(TokenAmount other) {
        return this.value <= other.value ? this : other;
    }

    /**
     * Returns {@code true} if this amount is strictly positive.
     *
     * @return {@code true} when value &gt; 0
     */
    public boolean isPositive() {
        return value > 0;
    }
}
