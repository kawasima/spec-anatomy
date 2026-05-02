package org.tw.token_billing.shell.persistence;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;
import org.tw.token_billing.core.model.Customer;
import org.tw.token_billing.core.model.CustomerId;
import org.tw.token_billing.core.port.CustomerRepository;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.tw.token_billing.shell.persistence.MapBillDecoders.CUSTOMER_ROW;

/**
 * JdbcClient-backed implementation of the Core's {@link CustomerRepository} port.
 *
 * <p>The Core declares only the existence-check responsibility ({@code findById}),
 * so this repository deliberately stays read-only. Insert / update operations
 * are out of scope for the spec model (Customer CRUD is Scope Out per the
 * source-material AC list).
 */
@Repository
public class PgCustomerRepository implements CustomerRepository {

    private final JdbcClient jdbc;

    public PgCustomerRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public Optional<Customer> findById(CustomerId id) {
        List<Map<String, Object>> rows = jdbc
                .sql("SELECT id, name FROM customers WHERE id = ?")
                .param(id.value())
                .query()
                .listOfRows();
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(CUSTOMER_ROW.decode(rows.getFirst()).getOrThrow());
    }
}
