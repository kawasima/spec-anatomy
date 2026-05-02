package org.tw.token_billing.shell.api;

import net.unit8.raoh.Err;
import net.unit8.raoh.Ok;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.tw.token_billing.shell.api.JsonUsageDecoders.UsageReportCommand;
import org.tw.token_billing.shell.service.UsageBillingService;
import tools.jackson.databind.JsonNode;

import java.util.Map;

import static org.tw.token_billing.shell.api.JsonUsageDecoders.USAGE_REPORT_REQUEST;

/**
 * Single-endpoint controller for {@code POST /api/usage}.
 *
 * <p>The controller does three things and only three things:
 * <ol>
 *   <li>Decode the JSON body into a {@link UsageReportCommand} via
 *       {@link JsonUsageDecoders#USAGE_REPORT_REQUEST}.</li>
 *   <li>Hand the command to {@link UsageBillingService#process} and let
 *       it run the spec-model workflow against the Core.</li>
 *   <li>Translate the {@link UsageBillingService.Result} sealed type into
 *       the matching HTTP status via {@link ApiErrorMapper}, encoding
 *       successful bills with {@link BillEncoder#BILL}.</li>
 * </ol>
 *
 * <p>No business logic lives here — the controller is a thin adapter
 * between HTTP and the workflow.
 */
@RestController
@RequestMapping("/api")
public class UsageController {

    private final UsageBillingService service;

    public UsageController(UsageBillingService service) {
        this.service = service;
    }

    /**
     * AC5: returns 201 Created with the calculated bill on success.
     * AC1 → 404, AC2 → 400, missing-subscription → 409.
     */
    @PostMapping("/usage")
    public ResponseEntity<?> reportUsage(@RequestBody JsonNode body) {
        return switch (USAGE_REPORT_REQUEST.decode(body)) {
            case Ok<UsageReportCommand>(var cmd)   -> handle(cmd);
            case Err<UsageReportCommand>(var iss) -> ApiErrorMapper.badRequest(iss);
        };
    }

    private ResponseEntity<?> handle(UsageReportCommand cmd) {
        return switch (service.process(cmd)) {
            case UsageBillingService.Result.Calculated(var bill) -> {
                Map<String, Object> body = BillEncoder.BILL.encode(bill);
                yield ResponseEntity.status(HttpStatus.CREATED).body(body);
            }
            case UsageBillingService.Result.CustomerNotFound(var cid) ->
                    ApiErrorMapper.customerNotFound(cid);
            case UsageBillingService.Result.SubscriptionInactive(var cid) ->
                    ApiErrorMapper.subscriptionInactive(cid);
            case UsageBillingService.Result.DataIntegrityIssue(var detail) ->
                    ApiErrorMapper.internalError(detail);
        };
    }
}
