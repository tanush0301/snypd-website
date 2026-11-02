# ops/stock

Snapshot of the frozen Stock design dataset, exported 30 Oct 2026 by the backend repo
(`snypd_codebase/ops/stock_tests/export_acceptance.cjs`, from `design-stock/stock-data.js`):

- `acceptance-fixture.json`: 215 live items + 3 recently-deleted copies + 580 history rows (logical write order), "today" = 2026-10-27.
- `acceptance-oracle.json`: the numbers the design computes from those rows, in cents. The SQL migrations 065-068 reproduce them exactly
  (backend `ops/stock_tests/run_tests.sh`), and `ops/test_stock_core.cjs` checks the JS engine (`ops/stock_engine.js`) against the same file.

Never edit these by hand. Re-export from the backend repo and copy both files over when the design dataset changes.
`ops/` is in `.vercelignore`: nothing here is deployed.
