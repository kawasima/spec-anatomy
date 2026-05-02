package org.tw.token_billing.shell.api;

import net.unit8.raoh.decode.Decoder;
import net.unit8.raoh.json.JsonDecoder;
import org.tw.token_billing.core.model.CustomerId;
import org.tw.token_billing.core.model.TokenAmount;
import tools.jackson.databind.JsonNode;

import static net.unit8.raoh.json.JsonDecoders.*;

/**
 * JSON-boundary decoders for the usage-billing API.
 *
 * <p>Decodes {@code POST /api/usage} request bodies into the
 * {@link UsageReportCommand} record. Token-non-negativity (spec model AC2)
 * is enforced declaratively via {@code long_().nonNegative()}, which produces
 * a {@code TokenAmount} whose value-type constructor itself refuses negatives.
 *
 * <p>This decoder does <em>not</em> perform the customer-existence check.
 * That check is I/O — it requires hitting the customer table — and pulling it
 * into the boundary decoder would force the decoder to depend on
 * {@code CustomerRepository}, blurring the line between syntactic decoding
 * and business validation. The check happens once in {@code UsageController},
 * mapped to a 404 (AC1).
 */
public final class JsonUsageDecoders {

    private JsonUsageDecoders() {}

    /**
     * Decodes the {@code POST /api/usage} request body.
     *
     * <pre>{@code
     * {
     *   "customerId": "cust-123",
     *   "promptTokens": 30000,
     *   "completionTokens": 0
     * }
     * }</pre>
     *
     * <p>Errors are accumulated across all three fields rather than
     * short-circuiting on the first one — a malformed request that gets
     * three errors at once produces a single 400 with all of them.
     */
    public static final JsonDecoder<UsageReportCommand> USAGE_REPORT_REQUEST = wrapJson(
            combine(
                    field("customerId",       string().trim().nonBlank()).map(CustomerId::new),
                    field("promptTokens",     long_().nonNegative()).map(TokenAmount::new),
                    field("completionTokens", long_().nonNegative()).map(TokenAmount::new)
            ).map(UsageReportCommand::new));

    /**
     * Decoded usage-report command — a {@link CustomerId} that is not yet
     * verified (existence check happens in the service) plus two
     * non-negative token counts (already enforced by the value type).
     *
     * @param customerId       the raw customer id from the request body
     * @param promptTokens     non-negative prompt tokens
     * @param completionTokens non-negative completion tokens
     */
    public record UsageReportCommand(
            CustomerId customerId,
            TokenAmount promptTokens,
            TokenAmount completionTokens
    ) {}

    private static <T> JsonDecoder<T> wrapJson(Decoder<JsonNode, T> dec) {
        return dec::decode;
    }
}
