package org.tw.token_billing.shell.api;

import net.unit8.raoh.Issues;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Maps API failures to HTTP responses.
 *
 * <p>Three distinct failure shapes show up at the API boundary:
 * <ul>
 *   <li><strong>Decoder issues</strong> — JSON-shape errors and
 *       {@code TokenAmount}-non-negativity errors raised by Raoh. AC2
 *       maps these to <strong>HTTP 400</strong> with a structured
 *       {@code issues} list.</li>
 *   <li><strong>Customer-not-found</strong> — AC1 maps this to
 *       <strong>HTTP 404</strong> with a message-only body. The AC text
 *       ({@code "Customer not found"}) is reproduced verbatim.</li>
 *   <li><strong>Subscription-inactive</strong> — the spec model adds
 *       {@code サブスクリプション無効エラー} (a Core failure case). The
 *       Shell maps this to <strong>HTTP 409 Conflict</strong>: the
 *       customer exists but is not in a billable state right now.</li>
 * </ul>
 *
 * <p>The body shapes are kept simple on purpose. The {@code Issues}
 * structure already gives clients a {@code path / code / message}
 * triple — that is the structured contract for validation errors.
 * The non-validation cases use a flat object with a {@code code} and
 * a {@code message} so clients can branch on the code without parsing
 * a free-text message.
 */
public final class ApiErrorMapper {

    private ApiErrorMapper() {}

    /** AC2: token-count violations / malformed JSON → 400 with all issues. */
    public static ResponseEntity<Map<String, Object>> badRequest(Issues issues) {
        var body = new LinkedHashMap<String, Object>();
        body.put("issues", issues.toJsonList());
        body.put("errors", issues.flatten());
        return ResponseEntity.badRequest().body(body);
    }

    /** AC1: customer id refers to a non-existent customer. */
    public static ResponseEntity<Map<String, Object>> customerNotFound(String customerId) {
        var body = new LinkedHashMap<String, Object>();
        body.put("code",       "customer_not_found");
        body.put("message",    "Customer not found");
        body.put("customerId", customerId);
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    /**
     * Spec-model addition: customer exists but has no active subscription
     * at the calculation time. 409 because the conflict is between the
     * request and the persistent state of the customer.
     */
    public static ResponseEntity<Map<String, Object>> subscriptionInactive(String customerId) {
        var body = new LinkedHashMap<String, Object>();
        body.put("code",       "subscription_inactive");
        body.put("message",    "Customer has no active subscription at this time");
        body.put("customerId", customerId);
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    /**
     * Internal error fallback used when an invariant of the persisted data
     * is broken. The bill row reaches the calculation pipeline only after
     * the table CHECK constraints have accepted it, so this is genuinely
     * "should not happen"; we still surface it as 500 rather than crashing
     * silently. This is the only place exceptions are translated to HTTP.
     */
    public static ResponseEntity<Map<String, Object>> internalError(String detail) {
        var body = new LinkedHashMap<String, Object>();
        body.put("code",    "internal_error");
        body.put("message", detail);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);
    }

    /**
     * Convenience: build a single-issue 400 from a path / code / message,
     * reusing the same body shape as {@link #badRequest(Issues)}. Used by
     * places (the controller's plan-projection step) that produce a
     * single business-level validation error.
     */
    public static ResponseEntity<Map<String, Object>> badRequestSingle(String path, String code, String message) {
        var item = Map.of(
                "path", path,
                "code", code,
                "message", message,
                "meta", Map.of()
        );
        var body = new LinkedHashMap<String, Object>();
        body.put("issues", List.of(item));
        body.put("errors", Map.of(path, List.of(message)));
        return ResponseEntity.badRequest().body(body);
    }
}
