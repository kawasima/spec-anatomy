package org.tw.token_billing.core.model;

/**
 * A usage report whose customer id has been verified and whose token counts
 * are guaranteed non-negative by the {@link TokenAmount} value type.
 *
 * <p>Corresponds to
 * {@code data 検証済み使用申告 = 検証済み顧客ID AND プロンプトトークン数 AND 完了トークン数}
 * in the spec model.
 *
 * <p>Bill calculation accepts only this validated form, which is what makes
 * the calculation a total function (no error case).
 *
 * @param customerId       the verified customer id
 * @param promptTokens     the prompt tokens consumed in this report
 * @param completionTokens the completion tokens consumed in this report
 */
public record ValidatedUsageReport(
        ValidatedCustomerId customerId,
        TokenAmount promptTokens,
        TokenAmount completionTokens
) {

    /**
     * Returns the total tokens for this report.
     *
     * <p>Encodes the invariant
     * {@code 総トークン数 = プロンプトトークン数 + 完了トークン数}.
     *
     * @return the sum of prompt and completion tokens
     */
    public TokenAmount totalTokens() {
        return promptTokens.plus(completionTokens);
    }
}
