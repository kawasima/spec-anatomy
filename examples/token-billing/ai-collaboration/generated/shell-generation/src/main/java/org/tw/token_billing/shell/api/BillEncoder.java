package org.tw.token_billing.shell.api;

import net.unit8.raoh.encode.Encoder;
import org.tw.token_billing.core.model.Bill;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Encoder from {@link Bill} to {@code Map<String, Object>} for HTTP response
 * bodies.
 *
 * <p>The output reflects the spec-model split. {@code InQuota} bills do not
 * carry an overage rate or a charge, and the encoded map omits those keys
 * entirely — not as nulls, not as zero. Clients that consume the response
 * see a structurally distinct shape and cannot accidentally treat
 * {@code totalCharge=0} as "in-quota" or {@code totalCharge=null} as
 * "field missing": the discriminator field {@code kind} is always present
 * and authoritative.
 *
 * <p>Why a separate {@link Encoder} per case rather than a single encoder
 * with conditional fields: the two cases are different shapes of data, and
 * giving each its own encoder mirrors the Core's sealed-interface split on
 * the wire. This is the same idea as the DB design (kind column + CHECK
 * constraints) applied to JSON.
 */
public final class BillEncoder {

    private BillEncoder() {}

    /**
     * Top-level encoder. Dispatches on the sealed {@link Bill} and delegates
     * to the case-specific encoder.
     */
    public static final Encoder<Bill, Map<String, Object>> BILL = bill -> switch (bill) {
        case Bill.InQuota in     -> IN_QUOTA.encode(in);
        case Bill.WithOverage wo -> WITH_OVERAGE.encode(wo);
    };

    private static final Encoder<Bill.InQuota, Map<String, Object>> IN_QUOTA = bill -> {
        var m = new LinkedHashMap<String, Object>();
        m.put("kind",                "IN_QUOTA");
        m.put("billId",              bill.id().value().toString());
        m.put("customerId",          bill.customerId().value().value());
        m.put("appliedPricingPlanId", bill.appliedPricingPlanId().value());
        m.put("promptTokens",        bill.promptTokens().value());
        m.put("completionTokens",    bill.completionTokens().value());
        m.put("totalTokens",         bill.totalTokens().value());
        m.put("includedTokensUsed",  bill.quotaConsumedTokens().value());
        // Why no overageTokens / overageRate / totalCharge fields here: the
        // spec model defines 枠内請求 as a record without those fields. Emitting
        // them as 0 / null would re-introduce the sentinel-zero ambiguity the
        // type split was meant to eliminate.
        m.put("calculatedAt",        bill.calculatedAt().toString());
        return m;
    };

    private static final Encoder<Bill.WithOverage, Map<String, Object>> WITH_OVERAGE = bill -> {
        var m = new LinkedHashMap<String, Object>();
        m.put("kind",                       "WITH_OVERAGE");
        m.put("billId",                     bill.id().value().toString());
        m.put("customerId",                 bill.customerId().value().value());
        m.put("appliedPricingPlanId",       bill.appliedPricingPlanId().value());
        m.put("promptTokens",               bill.promptTokens().value());
        m.put("completionTokens",           bill.completionTokens().value());
        m.put("totalTokens",                bill.totalTokens().value());
        m.put("includedTokensUsed",         bill.quotaConsumedTokens().value());
        m.put("overageTokens",              bill.overageTokens().value());
        m.put("appliedOverageRatePer1K",    bill.appliedOverageRatePer1K().amount());
        m.put("totalCharge",                bill.totalCharge().amount());
        m.put("calculatedAt",               bill.calculatedAt().toString());
        return m;
    };
}
