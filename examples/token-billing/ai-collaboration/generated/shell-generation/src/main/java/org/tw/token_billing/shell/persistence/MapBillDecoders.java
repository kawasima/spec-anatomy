package org.tw.token_billing.shell.persistence;

import net.unit8.raoh.decode.Decoder;
import org.tw.token_billing.core.model.Bill;
import org.tw.token_billing.core.model.BillId;
import org.tw.token_billing.core.model.Customer;
import org.tw.token_billing.core.model.CustomerId;
import org.tw.token_billing.core.model.Money;
import org.tw.token_billing.core.model.OverageTokens;
import org.tw.token_billing.core.model.PricingPlan;
import org.tw.token_billing.core.model.PricingPlanId;
import org.tw.token_billing.core.model.Subscription;
import org.tw.token_billing.core.model.SubscriptionId;
import org.tw.token_billing.core.model.TokenAmount;
import org.tw.token_billing.core.model.ValidatedCustomerId;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Map;
import java.util.Optional;

import static net.unit8.raoh.decode.ObjectDecoders.*;
import static net.unit8.raoh.decode.map.MapDecoders.*;

/**
 * Map-boundary decoders for the persistence layer.
 *
 * <p>Each constant decodes a {@code Map<String, Object>} row — the format
 * returned by Spring JDBC's {@code JdbcClient.query().listOfRows()} — into a
 * Core domain record. There are no {@code @Entity} classes; the Core records
 * themselves are the persistence target, and the layer-crossing is one decode
 * per row.
 *
 * <p>The {@link #BILL_ROW} decoder uses the {@code kind} discriminator to
 * dispatch to either {@link Bill.InQuota} or {@link Bill.WithOverage}, which
 * mirrors the sealed-interface case split on the Core side. The discriminator
 * column is the database expression of the type split documented in
 * {@code adrs/ADR-003-bill-table-design.md}.
 */
public final class MapBillDecoders {

    private MapBillDecoders() {}

    // ─── Customer / PricingPlan / Subscription ──────────────────────────

    /** {@code customers} row → {@link Customer}. */
    public static final Decoder<Map<String, Object>, Customer> CUSTOMER_ROW = combine(
            field("id",   string()).map(CustomerId::new),
            field("name", string())
    ).map(Customer::new);

    /** {@code pricing_plans} row → {@link PricingPlan}. */
    public static final Decoder<Map<String, Object>, PricingPlan> PRICING_PLAN_ROW = combine(
            field("id",                  string()).map(PricingPlanId::new),
            field("name",                string()),
            field("monthly_quota",       long_().nonNegative()).map(TokenAmount::new),
            field("overage_rate_per_1k", decimal().nonNegative()).map(Money::usd)
    ).map(PricingPlan::new);

    /** {@code customer_subscriptions} row → {@link Subscription}. */
    public static final Decoder<Map<String, Object>, Subscription> SUBSCRIPTION_ROW = combine(
            field("id",             uuid()).map(SubscriptionId::new),
            field("customer_id",    string()).map(CustomerId::new),
            field("plan_id",        string()).map(PricingPlanId::new),
            field("effective_from", localDate()),
            optionalLocalDate("effective_to")
    ).map(Subscription::new);

    // ─── Bill (sealed: InQuota | WithOverage) ───────────────────────────

    /**
     * {@code bills} row → {@link Bill}.
     *
     * <p>Dispatches on the {@code kind} column. For {@code IN_QUOTA} the
     * rate / charge columns are required to be NULL by the table CHECK
     * constraint, so we read them as optional and ignore them; for
     * {@code WITH_OVERAGE} they are required and decoded. The decoder relies
     * on {@link OverageTokens} and {@link Bill.WithOverage}'s constructors to
     * enforce the {@code overage >= 1} and {@code charge > 0} invariants —
     * the same invariants the table CHECKs guarantee at the storage layer.
     */
    public static final Decoder<Map<String, Object>, Bill> BILL_ROW = (in, path) -> {
        Object kind = in.get("kind");
        if ("WITH_OVERAGE".equals(kind)) {
            return WITH_OVERAGE_ROW.decode(in, path).map(b -> (Bill) b);
        }
        return IN_QUOTA_ROW.decode(in, path).map(b -> (Bill) b);
    };

    private static final Decoder<Map<String, Object>, Bill.InQuota> IN_QUOTA_ROW = combine(
            field("id",                      uuid()).map(BillId::new),
            field("customer_id",             string()).map(cid -> new ValidatedCustomerId(new CustomerId(cid))),
            field("applied_pricing_plan_id", string()).map(PricingPlanId::new),
            field("prompt_tokens",           long_().nonNegative()).map(TokenAmount::new),
            field("completion_tokens",       long_().nonNegative()).map(TokenAmount::new),
            field("calculated_at",           instant())
    ).map(Bill.InQuota::new);

    private static final Decoder<Map<String, Object>, Bill.WithOverage> WITH_OVERAGE_ROW = combine(
            field("id",                          uuid()).map(BillId::new),
            field("customer_id",                 string()).map(cid -> new ValidatedCustomerId(new CustomerId(cid))),
            field("applied_pricing_plan_id",     string()).map(PricingPlanId::new),
            field("prompt_tokens",               long_().nonNegative()).map(TokenAmount::new),
            field("completion_tokens",           long_().nonNegative()).map(TokenAmount::new),
            field("included_tokens_used",        long_().nonNegative()).map(TokenAmount::new),
            field("overage_tokens",              long_().min(1)).map(OverageTokens::new),
            field("applied_overage_rate_per_1k", decimal().nonNegative()).map(Money::usd),
            field("total_charge",                decimal().positive()).map(Money::usd),
            field("calculated_at",               instant())
    ).map(Bill.WithOverage::new);

    // ─── Object-level decoders for raw Object types JDBC returns ────────

    /**
     * Decodes a JDBC value to a {@link java.util.UUID}. Postgres' JDBC driver
     * returns {@code java.util.UUID}; H2 / other drivers may return a String.
     * Both shapes are handled.
     */
    private static Decoder<Object, java.util.UUID> uuid() {
        return (in, path) -> {
            if (in == null) {
                return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.REQUIRED, "is required");
            }
            if (in instanceof java.util.UUID u) {
                return net.unit8.raoh.Result.ok(u);
            }
            if (in instanceof String s) {
                try {
                    return net.unit8.raoh.Result.ok(java.util.UUID.fromString(s));
                } catch (IllegalArgumentException e) {
                    return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.INVALID_FORMAT,
                            "invalid uuid: " + s);
                }
            }
            return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.TYPE_MISMATCH,
                    "expected uuid",
                    Map.of("expected", "uuid", "actual", in.getClass().getSimpleName()));
        };
    }

    /**
     * Decodes a JDBC value to an {@link Instant}. Most drivers return
     * {@link Timestamp}; some return {@link Instant} or {@link java.time.OffsetDateTime}.
     */
    private static Decoder<Object, Instant> instant() {
        return (in, path) -> {
            if (in == null) {
                return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.REQUIRED, "is required");
            }
            if (in instanceof Instant i) {
                return net.unit8.raoh.Result.ok(i);
            }
            if (in instanceof Timestamp t) {
                return net.unit8.raoh.Result.ok(t.toInstant());
            }
            if (in instanceof java.time.OffsetDateTime odt) {
                return net.unit8.raoh.Result.ok(odt.toInstant());
            }
            return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.TYPE_MISMATCH,
                    "expected timestamp",
                    Map.of("expected", "timestamp", "actual", in.getClass().getSimpleName()));
        };
    }

    /** Decodes a JDBC value to a {@link LocalDate}. */
    private static Decoder<Object, LocalDate> localDate() {
        return (in, path) -> {
            if (in == null) {
                return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.REQUIRED, "is required");
            }
            if (in instanceof LocalDate d) {
                return net.unit8.raoh.Result.ok(d);
            }
            if (in instanceof java.sql.Date sd) {
                return net.unit8.raoh.Result.ok(sd.toLocalDate());
            }
            return net.unit8.raoh.Result.fail(path, net.unit8.raoh.ErrorCodes.TYPE_MISMATCH,
                    "expected date",
                    Map.of("expected", "date", "actual", in.getClass().getSimpleName()));
        };
    }

    /** Optional {@code DATE} column → {@link Optional} of {@link LocalDate}. */
    private static Decoder<Map<String, Object>, Optional<LocalDate>> optionalLocalDate(String name) {
        return (in, path) -> {
            if (in == null || !in.containsKey(name) || in.get(name) == null) {
                return net.unit8.raoh.Result.ok(Optional.empty());
            }
            return localDate().decode(in.get(name), path.append(name)).map(Optional::of);
        };
    }
}
